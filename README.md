# LogAnalyzer
Log viewer

forget this project --> use https://klogg.filimonov.dev instead

# Usage
* <code>python loganalyzer.py</code>
* <code>python loganalyzer.py \<logfile\></code>
* <code>python loganalyzer.py \<logfile\> -c \<configfile\></code>

# Functions

* \+ = Increase log level
* \- = Decrease log level
* Number 0..4 = set log level (0 = critical, 4 = debug)
* <x>-<y> = Show log level <x> and <y> lines before that (e.g 2-2 = show level 2 plus 2 lines before that)
* f \<term\> = find (and highlight) this term
* r = reset to full log file
* q = quit
