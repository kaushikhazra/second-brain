# Observe — #87

`python checks/docs/check_docs_agree.py` — extracts each claim that more than one shipped file makes and
compares them (cm backup, memory_self, rel_type set, synaptra version vs SYNAPTRA_VERSION, stability days,
lifespan words, launcher names in restart sentences); then puts one old contradiction back at a time and
requires the named AC to fail. Done = 7 of 7 hold and every put-back is caught.
