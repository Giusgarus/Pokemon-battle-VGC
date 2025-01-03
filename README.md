# Pokemon-battle-VGC
## Execution
The arguments passed with the command line are parsed by the program, which changes its behavior based on them.  
The syntax of the command to be executed is the following:

```bash
$ python Agents/pkm_battle.py -e <path_to_agent0.env> <path_to_agent1.env> -s <path_to_statistics.csv> -a <agent0> <agent1> -p <n> <param_1>=<value_1>:<type_1> ... <param_n>=<value_n>:<type_n>
'''

Explanation of Flags
-e (Environment flag): Specifies respectively the environment of agent0 and the one of agent1.
-s (Statistics flag): Specifies the path to the .csv file used to store the statistics (computed only for the first agent: agent0).
-a (Agents flag): Specifies agent0 and agent1.
-p (Parameters flag, optional): If used, specifies the number of parameters (n) and then the parameters themselves, which are passed to the class of agent0 that inherits from BattlePolicy.

$ python Agents/pkm_battle.py -e Agents/MiniMax/MiniMax.env Agents/Logic/Logic.env \
-s Agents/Statistics/MiniMax_vs.csv -a MiniMax Logic

 
