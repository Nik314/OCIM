import pandas
import datetime
import warnings

warnings.filterwarnings("ignore", category=pandas.errors.SettingWithCopyWarning)
example_log = pandas.DataFrame({"ocel:timestamp":[],"ocel:oid":[],"ocel:type":[],"ocel:activity":[],"ocel:eid":[]})


events = [
    ("identify",{"C1","E1"}),
    ("reject",{"C1","E1"}),
    ("identify", {"C1", "E1"}),
    ("reject",{"C1","E1"}),
    ("identify", {"C1", "E1"}),
    ("produce",{"I1"}),
    ("place",{"C1","O1","I1","I2"}),
    ("produce",{"O1","I2"}),
    ("send",{"O1","I2"}),
    ("place", {"C1", "O2", "I3", "I4"}),
    ("store", {"O1", "I1"}),
    ("produce", {"O2", "I3"}),
    ("produce", { "I5"}),
    ("produce", {"O2", "I4"}),
    ("confirm", {"C1", "O1", "I1", "I2"}),
    ("confirm", {"C1", "O2", "I3", "I4"}),
    ("send", {"O2", "I3"}),
    ("send", {"O2","I4"}),
    ("produce", {"I6"}),
    ("pay", {"C1", "O1", "I1", "I2"}),
    ("place", {"C1", "O3", "I5", "I6"}),
    ("store", {"O3","I5"}),
    ("pay", {"C1", "O2", "I3", "I4"}),
    ("confirm", {"C1", "O3", "I5", "I6"}),
    ("produce", {"I9"}),
    ("produce", {"I10"}),
    ("place", {"C1", "O4", "I7", "I8", "I9", "I10"}),
    ("store", {"O3", "I6"}),
    ("produce", {"O4", "I7"}),
    ("produce", {"O4", "I8"}),
    ("store", {"O4", "I8"}),
    ("send", {"O4", "I7"}),
    ("confirm", {"C1", "O4", "I7", "I8", "I9", "I10"}),
    ("pay", {"C1", "O3", "I5", "I6"}),
   ("produce", {"I11"}),
    ("pay", {"C1", "O4", "I7", "I8", "I9", "I10"}),
    ("store", {"O4", "I9"}),
    ("store", {"O4", "I10"}),
    ("produce", {"I12"}),
    ("place", {"C1", "O5", "I11", "I12"}),
    ("produce", {"I13"}),
    ("produce", {"I14"}),
    ("confirm", {"C1", "O5", "I11", "I12"}),
    ("send", {"O5", "I11"}),
    ("pay", {"C1", "O5", "I11", "I12"}),
    ("send", {"O5", "I12"}),
    ("place", {"C1", "O6", "I13", "I14"}),
    ("send", {"O6", "I13"}),
    ("confirm", {"C1", "O6", "I13", "I14"}),
    ("store", {"O6", "I14"}),
    ("pay", {"C1", "O6", "I13", "I14"}),
]


i = 0
for event in events:
    for oid in event[1]:
        example_log.loc[example_log.shape[0]] = [datetime.datetime.now()+datetime.timedelta(days=i), oid, oid[0],event[0],i]
    i += 1
    substring = ", ".join([f"\\texttt{{{str(oid[0]).lower()}}}_{{{oid[1:]}}}" for oid in sorted(list(event[1]))])
    print(f"\\textsc{{{event[0]}}} & $ \\{{{substring}\\}}$ &")

#print(i)
for ot in example_log["ocel:type"].unique():
    pass
    #print(ot)
    #pm4py.view_dfg(pm4py.discover_eventually_follows_graph(example_log[example_log["ocel:type"].isin([ot])],
    #    activity_key="ocel:activity", timestamp_key="ocel:timestamp",case_id_key="ocel:oid"),{},{})


#time.sleep(5)
#   & \textsc{pay}  &  $\{ \texttt{c}_1, \texttt{o}_4, \texttt{i}_7, \texttt{i}_8, \texttt{i}_9\},$


#example_log = example_log[example_log["ocel:activity"].isin(["pay","confirm","store","send"])]
div, con, rel = get_interaction_patterns([example_log])
#dfgs = get_cummulative_directly_follows_relation([example_log])
#clos = get_transitive_closure_follows_relation([example_log])
#detect_concurrent_cut([example_log],dfgs,clos,rel,div)

print_result(object_centric_inductive_miner([example_log], div, rel))

exit()

print(is_loop_cut_valid([example_log], [["identify"],["reject"]],dfgs,clos,rel,div))
print(is_concurrent_cut_valid([example_log], [["identify"],["reject"]],dfgs,clos,rel,div))
exit()

from OCIM.src import object_centric_inductive_miner, print_result

result = object_centric_inductive_miner(example_log, div, rel)
print_result(result)
