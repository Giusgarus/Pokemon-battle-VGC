import os
import sys
from dotenv import dotenv_values
from vgc.behaviour.BattlePolicies import BattlePolicy
from vgc.engine.PkmBattleEnv import PkmBattleEnv
from MCTS.MCTSBattlePolicies import MCTSBattlePolicy
from MiniMax.MiniMaxBattlePolicies import MiniMaxPlayer
from Logic.Logic_Agent import LogicPolicy
from Random.Random_Agent import RandomPolicy
from Combined.Combined_Agent import CombinedPolicy
from vgc.datatypes.Objects import Pkm, PkmMove


def retrive_args(flag: str, n_next_args=1) -> list:
    '''
    Retrieve a number of "n_next_args" command line arguments which follows the flag string "flag".
    
    Params:
    - flag: string which identifies any flag to be searched for (e.g. "-s").
    - n_next_args: number of arguments to be read after the flag.

    Returns:
    A list with the arguments retrieved after the flag.
    '''
    args = sys.argv
    for i, arg in enumerate(args):
        if arg == flag:
            try:
                args_to_ret = []
                for arg_to_ret in args[i+1:i+n_next_args+1]:
                    args_to_ret.append(arg_to_ret)
                return args_to_ret
            except:
                break
    return []

def write_metrics(metrics_dict: dict, params: dict):
    '''
    Write the metrics and the parameters of the battle in the file .csv identified by the argument \
    associated to the flag "-s".
    
    Params:
    - metrics_dict: dictionary with metrics values obtained by the battle.
    - params: dictionary with parameters used in the battle.
    '''
    data_to_write = {}
    # Retrieve args from CLI
    file_path = retrive_args(flag='-s')[0]
    agents = retrive_args(flag='-a', n_next_args=2)
    # Add the agents to the dictionary
    data_to_write['agent0'] = agents[0]
    data_to_write['agent1'] = agents[1]
    # Add the parameters' to the dictionary
    for key, value in params.items():
        data_to_write[key] = value
    # Add the metrics' to the dictionary
    for key, value in metrics_dict.items():
        data_to_write[key] = value
    # Case of empty file (or which not exists)
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        columns_str = ''
        for key in data_to_write.keys():
            columns_str += f'{key};'
        columns_str = columns_str[:-1] + '\n'
        with open(file_path, 'w') as f:
            f.write(columns_str)
    # Create the row to be append to the file
    str_to_write = ''
    for key, value in data_to_write.items():
        str_to_write += f'{value};'
    str_to_write = str_to_write[:-1] + '\n'
    # Write on the file the dataframe created
    with open(file_path, 'a') as f:
        f.write(str_to_write)
    return
        

def get_parameters_from_env() -> tuple:
    '''
    Retrieve the parameters from the environment files associated with the two players, \
    which are passed as arguments in the command line (with flag "-e" and the path for both \
    the .env files) in the same order of the agents' argsuments. \
    e.g. "-a MCTS Logic -e ./Agents/MCTS/MCTS.env ./Agents/Logic/Logic.env"

    Returns:
    A tuple with 2 dictionaries: the first for the parameters of the player 0, the second for \
    the parameters of the player 1.
    '''
    def get_params(env_keys_dict: dict) -> dict:
        '''
        Given the dictionary of associations <key:string_with_comma_separated_values>, \
        build a dictionary of associations <key:python_values_list>.
        '''
        for key, value in env_keys_dict.items():
            env_keys_dict[key] = value.replace(' ', '')
        params = {}
        for key in env_keys_dict['KEYS'].split(','):
            if env_keys_dict[key+'_TYPE'] == 'int':
                key_type = int
            elif env_keys_dict[key+'_TYPE'] == 'float':
                key_type = float
            elif env_keys_dict[key+'_TYPE'] == 'bool':
                key_type = bool
            else:
                key_type = str
            try:
                params[key] = [key_type(val) for val in env_keys_dict[key].split(',')]
            except:
                print(f'Error parsing {key} in.env file')
                return {}
        return params
    # Try to load the environment file for the first player
    p0_keys_dict = load_env(player_index=0)
    if not p0_keys_dict: return {}, {}
    params_player0 = get_params(p0_keys_dict)
    # Try to load the environment file for the second player
    p1_keys_dict = load_env(player_index=1)
    if not p1_keys_dict: return params_player0, {}
    params_player1 = get_params(p1_keys_dict)
    return params_player0, params_player1

def load_env(player_index=0) -> bool:
    '''
    Load the environment file associated with the player passed as parameter (requires the "-e" arguments by CLI).

    Params:
    - player_index: index of the player (0 or 1).

    Returns:
    A dictionary with the keys and values of the environment file.
    '''
    args = retrive_args(flag='-e', n_next_args=2)
    if len(args) != 2:
        print(f'Usage:\n- Command: {sys.argv[0]} -e first_agent.env second_agent.env -a first_agent second_agent -s statistics_path\n- Agents: Random, Logic, MiniMax, MCTS, Combined.\n- Statistics: computed only for the first agent passed as parameter.')
        return False
    return dotenv_values(args[player_index])

def get_agents() -> tuple[BattlePolicy|None, BattlePolicy|None]:
    '''
    Returns:
    A tuple with the two agents as instances of BattlePolicy class corresponding to the agents passed as
    arguments in the command line.\n
    If the agents are not passed as arguments, it returns None, None.\n
    If the agents need some arguments they should be passed as arguments in the command line as follows:
    "-p key1=value1 key2=value2 ... keyN=valueN".\n
    Possible agents: Random, Logic, MiniMax, MCTS, Combined.
    '''
    agents_dict = {
        'Random': RandomPolicy,
        'Logic': LogicPolicy,
        'MiniMax': MiniMaxPlayer,
        'MCTS': MCTSBattlePolicy,
        'Combined': CombinedPolicy
    }
    agents = retrive_args(flag='-a', n_next_args=2)
    try:
        n_params = retrive_args(flag='-p', n_next_args=1)[0]
        keys_values = retrive_args(flag='-p', n_next_args=n_params+1)[1:]
    except:
        keys_values = []
    params_dict = {}
    for key_value in keys_values:
        key, value = key_value.split('=')
        params_dict[key] = value
    if agents == []:
        print(f'Usage:\n- Command: {sys.argv[0]} -e first_agent.env second_agent.env -a first_agent second_agent -s statistics_path -p p1=v1 pN=vN\n- Agents: {[e for e in agents_dict.keys()]}.\n- Statistics: computed only for the first agent passed as parameter.')
        return None, None
    try:
        params_dict['player_index'] = 0
        agent0 = agents_dict[agents[0]](**params_dict)
        #print(f'First agent with parameters:\n{agent0}') # debug
    except:
        try:
            agent0 = agents_dict[agents[0]]()
            #print(f'First agent with NO parameters:\n{agent0}') # debug
        except:
            print(f'Usage:\n- Command: {sys.argv[0]} -e first_agent.env second_agent.env -a first_agent second_agent -s statistics_path -p p1=v1 pN=vN\n- Agents: {[e for e in agents_dict.keys()]}.\n- Statistics: computed only for the first agent passed as parameter.')
            return None, None
    try:
        agent1 = agents_dict[agents[1]](1)
        #print(f'Second agent with parameters:\n{agent1}') # debug
    except:
        try:
            agent1 = agents_dict[agents[1]]()
            #print(f'First agent with NO parameters:\n{agent1}') # debug
        except:
            print(f'Usage:\n- Command: {sys.argv[0]} -e first_agent.env second_agent.env -a first_agent second_agent -s statistics_path -p p1=v1 pN=vN\n- Agents: {[e for e in agents_dict.keys()]}.\n- Statistics: computed only for the first agent passed as parameter.')
            return None, None
    return agent0, agent1

def get_params_combinations(params: dict) -> list[dict]:
    '''
    Creates and saves into the class instance a list with all the possible combinations of parameters \
    in the dictionary "params".

    Parameters:
    - params: dictionary with the parameters as associations <key:values> (with: key=parameter_name,
    values=possible_values_list).

    Returns:
    A list with a dictionary for each element which represents a combination of parameters (1 combination = 1 dictionary).
    '''
    params_index_dict = {}
    params_combinations = []
    for key in params.keys():
        params_index_dict[key] = 0 # current_index for that key
    while sum([index+1 for _, index in params_index_dict.items()]) != sum(len(val_list) for _, val_list in params.items()):
        params_i = {}
        for key, i in params_index_dict.items():
            params_i[key] = params[key][i]
        params_combinations.append(params_i)
        for key in params_index_dict.keys():
            params_index_dict[key] += 1
            if params_index_dict[key] < len(params[key]):
                break
            params_index_dict[key] = 0
    params_i = {}
    for key, i in params_index_dict.items():
        params_i[key] = params[key][i]
    params_combinations.append(params_i)
    return params_combinations

def run_battle(player0: BattlePolicy, player1: BattlePolicy, env: PkmBattleEnv, mode='console') -> dict:
    '''
    Performs a single battle between the two players "player0" and "player1" in the environment "env".

    Params:
    - player0: the first player as instance of BattlePolicy class.
    - player1: the second player as instance of BattlePolicy class.
    - env: environmento of the battle as instance of PkmBattleEnv class.
    - mode: string which identifies the output modality (e.g. 'console', 'ux').

    Returns:
    A dictionary with the metrics of the battle for the first player's view with the following keys:\n
    - 'n_turns': number of turns of the battle.\n
    - 'n_switches': number of switches of the first player (player0 has to be implemented a self.n_switches \
    variable where is saved this information).\n
    - 'hp_residue': percentage of the total HP of the first player's team which remains at the end of the battle.\n
    - 'winner': the winner of the battle (0 if the first player wins, 1 if the second player wins).
    '''
    # Reset the environment to get the initial state
    states, _ = env.reset()
    env.render(mode)
    # Perform a single battle until it's terminated
    index = 0
    terminated = False
    while not terminated:
        my_action = player0.get_action(states[0])
        opp_action = player1.get_action(states[1])
        try:
            player0.generate_tree(id=index)
        except:
            pass
        states, _, terminated, _, _ = env.step([my_action,opp_action])
        env.render(mode)
        index += 1
    # Get the metrics of the battle for player 0
    metrics_dict: dict = {}
    metrics_dict['n_turns'] = index
    metrics_dict['n_switches'] = player0.n_switches
    pkm_list = [env.teams[0].active] + [pkm for pkm in env.teams[0].party]
    hp_resudue = tot_hp = 0
    for pkm in pkm_list:
        hp_resudue += pkm.hp
        tot_hp += pkm.max_hp
    metrics_dict['hp_residue'] = round(number=(100/tot_hp) * hp_resudue, ndigits=2)
    metrics_dict['winner'] = env.winner
    return metrics_dict