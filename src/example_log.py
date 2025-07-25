import pandas
import datetime
import pm4py

example_log = pandas.DataFrame({"ocel:timestamp":[],"ocel:oid":[],"ocel:type":[],"ocel:activity":[],"ocel:eid":[]})

events = [

    ("identify",{"C1"}),
    ("reject",{"C1"}),
    ("identify", {"C1"}),
    ("place",{"C1","O1","I1","I2"}),
    ("place", {"C1", "O2", "I3", "I4"}),
    ("produce", {"O1","I1","C1"}),
    ("produce",{"O1","I2","C1"}),
    ("pay", {"C1", "O1", "I1", "I2"}),
    ("pay", {"C1", "O2", "I3", "I4"}),
    ("produce", {"O2", "I3"}),
    ("produce", {"O2", "I4"}),
    ("place", {"C1", "O3", "I5", "I6"}),
    ("produce", {"O3", "I6"}),
    ("pay", {"C1", "O3", "I5", "I6"}),
    ("produce", {"O3", "I5","C1"}),
    ("place", {"C1", "O4", "I7", "I8"}),
    ("identify", {"C2"}),
    ("produce", {"O4", "I7"}),
    ("produce", {"O4", "I8"}),
    ("place", {"C2", "O5", "I9"}),
    ("pay", {"C1", "O4", "I7", "I8"}),
    ("store", {"O1", "I1"}),
    ("store", {"O1", "I2"}),
    ("pay", {"C2", "O5", "I9"}),
    ("store", {"O2", "I3"}),
    ("send", {"O2","I4"}),
    ("send", {"O3","I5"}),
    ("produce", {"C2", "O5", "I9"}),
    ("store", {"O3", "I6"}),
    ("send", {"O4", "I8"}),
    ("send", {"O4", "I7"}),
    ("send", {"O5", "I9"}),
]

i = 0
for event in events:
    for oid in event[1]:
        example_log.loc[example_log.shape[0]] = [datetime.datetime.now()+datetime.timedelta(days=i), oid, oid[0],event[0],i]
    i += 1
    substring = ", ".join([f"\\texttt{{{str(oid[0]).lower()}}}_{{{oid[1:]}}}" for oid in sorted(list(event[1]))])
    print(f"\\textsc{{{event[0]}}} & $ \\{{{substring}\\}}$ &")

print(example_log)
from src import apply
print(apply("", input_log=example_log)[0])
exit()


for ot in example_log["ocel:type"].unique():
    print(ot)
    print(example_log[example_log["ocel:type"] ==ot]["ocel:oid"].unique())
    pm4py.view_dfg(*pm4py.discover_dfg(example_log[example_log["ocel:type"].isin([ot])],
        activity_key="ocel:activity", timestamp_key="ocel:timestamp",case_id_key="ocel:oid"))

