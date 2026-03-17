import json
import glob
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

data_dir = r"c:\Blake\Coding Stuff\box-box-box\data\historical_races"
files = glob.glob(os.path.join(data_dir, "*.json"))

races = []
for f in files[:8]:
    with open(f, 'r') as fin:
        races.extend(json.load(fin))

class RaceDataset(Dataset):
    def __init__(self, races):
        self.races = races
        
        # We will extract pairwise comparisons
        self.pairs = []
        for race in self.races:
            config = race['race_config']
            strats = {s['driver_id']: s for _, s in race['strategies'].items()}
            finishing = race['finishing_positions']
            
            # Precompute stints for each driver
            d_stints = {}
            for d in finishing:
                strat = strats[d]
                laps = []
                current_lap = 1
                current_tire = strat['starting_tire']
                
                for stop in strat['pit_stops']:
                    pit_lap = stop['lap']
                    stint_len = pit_lap - current_lap + 1
                    laps.append((current_tire, stint_len))
                    current_lap = pit_lap + 1
                    current_tire = stop['to_tire']
                    
                if current_lap <= config['total_laps']:
                    laps.append((current_tire, config['total_laps'] - current_lap + 1))
                    
                d_stints[d] = {
                    'laps': laps,
                    'pits': len(strat['pit_stops']),
                    'base_lap': config['base_lap_time'],
                    'plt': config['pit_lane_time'],
                    'temp': config['track_temp'],
                    'total_laps': config['total_laps']
                }
                
            for i in range(len(finishing)):
                for j in range(i+1, len(finishing)):
                    d1 = finishing[i]
                    d2 = finishing[j]
                    self.pairs.append((d_stints[d1], d_stints[d2]))
                    
    def __len__(self):
        return len(self.pairs)
        
    def __getitem__(self, idx):
        return self.pairs[idx]

def extract_laps_tensor(stint_data):
    # Returns [N_laps, 4] -> (compound_idx, age, temp, base_lap)
    laps_list = []
    
    temp = stint_data['temp']
    base_lap = stint_data['base_lap']
    
    for tire, slen in stint_data['laps']:
        c_idx = 0 if tire == 'SOFT' else (1 if tire == 'MEDIUM' else 2)
        for age in range(1, slen + 1):
            laps_list.append([c_idx, age, temp, base_lap])
            
    return torch.tensor(laps_list, dtype=torch.float32), stint_data['pits'] * stint_data['plt']

class LapTimeNet(nn.Module):
    def __init__(self):
        super().__init__()
        # Input features: [S, M, H, age, temp, base_lap]
        self.net = nn.Sequential(
            nn.Linear(6, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        
    def forward(self, x):
        # x is [B, N_laps, 4] -> c_idx, age, temp, base_lap
        B, N, _ = x.shape
        c_idx = x[..., 0].long()
        compounds = torch.nn.functional.one_hot(c_idx, num_classes=3).float()
        
        # Concat: [S, M, H, age, temp, base_lap]
        features = torch.cat([compounds, x[..., 1:]], dim=-1)
        
        lap_times = self.net(features).squeeze(-1) # [B, N_laps]
        total_times = lap_times.sum(dim=-1) # [B]
        return total_times

# Custom DataLoader logic
dataset = RaceDataset(races[:400]) # 400 races * 190 pairs = 76000 pairs
print(f"Dataset pairs: {len(dataset)}")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = LapTimeNet().to(device)
optimizer = optim.Adam(model.parameters(), lr=0.01)

# Margin ranking loss
# We want T1 < T2, so T2 - T1 > margin
margin = 0.5
criterion = nn.MarginRankingLoss(margin=margin)

# Training loop
epochs = 5
batch_size = 256

for ep in range(epochs):
    model.train()
    
    # Simple manual batching
    indices = np.random.permutation(len(dataset))
    
    total_loss = 0
    correct = 0
    
    for i in range(0, len(indices), batch_size):
        batch_idx = indices[i:i+batch_size]
        
        batch_d1, batch_d2 = [], []
        pits_1, pits_2 = [], []
        
        for idx in batch_idx:
            item1, item2 = dataset[idx]
            t1, p1 = extract_laps_tensor(item1)
            t2, p2 = extract_laps_tensor(item2)
            batch_d1.append(t1)
            batch_d2.append(t2)
            pits_1.append(p1)
            pits_2.append(p2)
            
        t1 = torch.stack(batch_d1).to(device)
        t2 = torch.stack(batch_d2).to(device)
        p1 = torch.tensor(pits_1, dtype=torch.float32).to(device)
        p2 = torch.tensor(pits_2, dtype=torch.float32).to(device)
        
        optimizer.zero_grad()
        
        tt1 = model(t1) + p1
        tt2 = model(t2) + p2
        
        # We want tt1 < tt2, so y=1 means input1 > input2?
        # MarginRankingLoss(x1, x2, y) -> max(0, -y * (x1 - x2) + margin)
        # We pass x1=tt2, x2=tt1, y=1 (meaning tt2 should be > tt1)
        target = torch.ones(t1.size(0)).to(device)
        
        loss = criterion(tt2, tt1, target)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item() * len(batch_idx)
        correct += (tt1 < tt2).sum().item()
        
    acc = correct / len(dataset)
    print(f"Epoch {ep+1}/{epochs} | Loss: {total_loss/len(dataset):.4f} | Acc: {acc:.4f}")

# EXPORT CURVES!
model.eval()
with torch.no_grad():
    print("\n--- EXTRACTED TIRE CURVES ---")
    age_range = torch.arange(1, 41, dtype=torch.float32)
    temp = 30.0
    base_lap = 80.0
    
    # For SOFT
    c_idx = torch.zeros(40)
    x = torch.stack([c_idx, age_range, torch.full((40,), temp), torch.full((40,), base_lap)], dim=1).unsqueeze(0).to(device)
    soft_curve = model(x).cpu().numpy()[0] / 40.0 # Just getting individual outputs actually requires modifying forward
    
    # We want individual lap times!
    features = torch.cat([
        torch.nn.functional.one_hot(c_idx.long(), num_classes=3).float().to(device),
        x[0, :, 1:].to(device)
    ], dim=-1)
    lap_times_soft = model.net(features).squeeze(-1).cpu().numpy()
    
    print("Soft Lap Times (Age 1-40, Temp=30):")
    print(np.round(lap_times_soft, 3))
    
    c_idx = torch.ones(40)
    x = torch.stack([c_idx, age_range, torch.full((40,), temp), torch.full((40,), base_lap)], dim=1).unsqueeze(0).to(device)
    features = torch.cat([
        torch.nn.functional.one_hot(c_idx.long(), num_classes=3).float().to(device),
        x[0, :, 1:].to(device)
    ], dim=-1)
    lap_times_medium = model.net(features).squeeze(-1).cpu().numpy()
    
    print("\nMedium Lap Times (Age 1-40, Temp=30):")
    print(np.round(lap_times_medium, 3))
    
    c_idx = torch.full((40,), 2)
    x = torch.stack([c_idx, age_range, torch.full((40,), temp), torch.full((40,), base_lap)], dim=1).unsqueeze(0).to(device)
    features = torch.cat([
        torch.nn.functional.one_hot(c_idx.long(), num_classes=3).float().to(device),
        x[0, :, 1:].to(device)
    ], dim=-1)
    lap_times_hard = model.net(features).squeeze(-1).cpu().numpy()
    
    print("\nHard Lap Times (Age 1-40, Temp=30):")
    print(np.round(lap_times_hard, 3))

