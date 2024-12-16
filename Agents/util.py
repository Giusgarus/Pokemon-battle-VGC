import os
import sys
from dotenv import load_dotenv
from vgc.behaviour.BattlePolicies import BattlePolicy
from vgc.engine.PkmBattleEnv import PkmBattleEnv
from MCTS.MCTSBattlePolicies import MCTSPlayer
from Logic_Agent import LogicPolicy
from Random_Agent import RandomPolicy


agents_dict = {
    'Random': RandomPolicy(player_index=1),
    'Logic': LogicPolicy(),
    'MiniMax': None,
    'MCTS': MCTSPlayer()
}

def retrive_arg(flag: str, n_next_args=1) -> str | list:
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

def write_statistics(winrate_str: str, params: dict, mode='a'):
    args = retrive_arg(flag='-s')
    # Cases of exit
    if args == []:
        return
    if params == {}:
        return
    # Create the parameters' string
    params_str = 'Parameters:\n'
    for key, value in params.items():
        params_str += f'\t{key}: {value}\n'
    # Check if the statistics already exist in the file to append there the new string (with a replacement)
    file_path = args[0]
    header = f'--- Statistics for {sys.argv[2]} ---\n\n'
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        if content == '':
            winrate_str = f'{header}{winrate_str}'
        elif params_str in content:
            content = content.replace(params_str, f'{winrate_str}\n{params_str}')
            with open(file_path, 'w') as f:
                f.write(content)
            return
    except FileNotFoundError:
        with open(file_path, 'w') as f:
            f.write(header)
    # Write the statistics in the file
    with open(file_path, mode) as f:
        f.write(f'\n\n{winrate_str}\n{params_str}')
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
    args = retrive_arg(flag='-e')
    if args == []:
        print(f'Usage:\n- Command: {sys.argv[0]} -e first_agent.env -a first_agent second_agent -s statistics_path\n- Agents: {[e for e in agents_dict.keys()]}.\n- Statistics: computed only for the first agent passed as parameter.')
        return False
    return load_dotenv(args[0])

def get_agents() -> tuple[BattlePolicy|None, BattlePolicy|None]:
    agents = retrive_arg(flag='-a', n_next_args=2)
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

def run_battle(player0: BattlePolicy, player1: BattlePolicy, env: PkmBattleEnv, mode='console') -> int:
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
    # Return the winner player of the battle
    return env.winner