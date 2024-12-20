import os
import sys
from dotenv import load_dotenv
from vgc.behaviour.BattlePolicies import BattlePolicy
from vgc.engine.PkmBattleEnv import PkmBattleEnv
from MCTS.MCTSBattlePolicies import MCTSBattlePolicy
from MiniMax.MiniMaxBattlePolicies import MiniMaxBattlePolicy
from Logic_Agent import LogicPolicy
from Random_Agent import RandomPolicy


agents_dict = {
    'Random': RandomPolicy(player_index=1),
    'Logic': LogicPolicy(),
    'MiniMax': MiniMaxBattlePolicy(depth=5),
    'MCTS': MCTSBattlePolicy()
}

def retrive_args(flag: str, n_next_args=1) -> list:
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
        

def get_parameters_from_env() -> dict | None:
    params = {}
    for key in os.getenv('KEYS').split(','):
        if os.getenv(key+'_TYPE') == 'int':
            key_type = int
        elif os.getenv(key+'_TYPE') == 'float':
            key_type = float
        elif os.getenv(key+'_TYPE') == 'bool':
            key_type = bool
        else:
            key_type = str
        try:
            params[key] = [key_type(val) for val in os.getenv(key).split(',')]
        except:
            print(f'Error parsing {key} in.env file')
            return None
    return params

def load_env() -> bool:
    args = retrive_args(flag='-e')
    if args == []:
        print(f'Usage:\n- Command: {sys.argv[0]} -e first_agent.env -a first_agent second_agent -s statistics_path\n- Agents: {[e for e in agents_dict.keys()]}.\n- Statistics: computed only for the first agent passed as parameter.')
        return False
    return load_dotenv(args[0])

def get_agents() -> tuple[BattlePolicy|None, BattlePolicy|None]:
    agents = retrive_args(flag='-a', n_next_args=2)
    if agents == []:
        print(f'Usage:\n- Command: {sys.argv[0]} -e first_agent.env -a first_agent second_agent -s statistics_path\n- Agents: {[e for e in agents_dict.keys()]}.\n- Statistics: computed only for the first agent passed as parameter.')
        return None, None
    try:
        agents_dict[agents[0]]
        agents_dict[agents[1]]
    except:
        print(f'Usage:\n- Command: {sys.argv[0]} -e first_agent.env -a first_agent second_agent -s statistics_path\n- Agents: {[e for e in agents_dict.keys()]}.\n- Statistics: computed only for the first agent passed as parameter.')
        return None, None
    return agents_dict[agents[0]], agents_dict[agents[1]]

def get_params_combinations(params: dict) -> list[dict]:
        '''
            Creates and saves into the class instance a list with all the possible combinations of parameters \
            in the dictionary \"params\".

            Parameters:
            - params: dictionary with parameters (keys = parameter_name, values = possible_values_list).

            Returns:
            A list with elements all the possible combinations of parameters as a dict (1 combination = 1 dictionary).
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
    Performs a single battle between two players and their teams in the environment passed as parameter.
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