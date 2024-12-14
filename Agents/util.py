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

def write_statistics(statistics_str: str, params: dict, mode='a'):
    dir_path = ''
    for elem in sys.argv[1].split('/')[:-1]:
        dir_path += elem + '/'
    with open(dir_path+'statistics.txt', mode) as f:
        f.write(statistics_str)
        f.write(f'Parameters:\n')
        for key, value in params.items():
            f.write(f'\t{key}: {value}\n')

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
    args = sys.argv
    try:
        with open(args[1]) as f:
            pass
    except:
        print(f'Usage:\n- Command: {args[0]} first_agent.env first_agent second_agent\n- Agents: {[e for e in agents_dict.keys()]}.\n- Statistics: computed only for the first agent passed as parameter.')
        return False
    return load_dotenv(args[1])

def get_agents() -> tuple[BattlePolicy|None, BattlePolicy|None]:
    args = sys.argv
    try:
        agents_dict[args[2]]
        agents_dict[args[3]]
    except:
        print(f'Usage:\n- Command: {args[0]} first_agent.env first_agent second_agent\n- Agents: {[e for e in agents_dict.keys()]}.\n- Statistics: computed only for the first agent passed as parameter.')
        return None, None
    return agents_dict[args[2]], agents_dict[args[3]]

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