import final_test_runner as ftr
test_data = ftr.load_data()

failed_names = []
for t, e_map in test_data:
    name = t['race_id'].lower() + '.json'
    predicted = ftr.manual_sim(r'data/test_cases/inputs/' + name)
    e = [k for k, v in sorted(e_map.items(), key=lambda item: item[1])]
    if predicted != e:
        failed_names.append(name)
        
print("Fails:", len(failed_names))
print(failed_names)
