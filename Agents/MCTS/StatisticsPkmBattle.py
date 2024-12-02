from vgc.behaviour.BattlePolicies import RandomPlayer
from vgc.datatypes.Objects import PkmTeam
from vgc.engine.PkmBattleEnv import PkmBattleEnv


def run_statistics_battle(player0: RandomPlayer, player1: RandomPlayer, env: PkmBattleEnv, mode='console') -> tuple:
    '''
    Performs a single battle between two players and their teams in the environment passed as parameter.

    Returns:
    A tuple with the statistics of the battle: (n_moves: int, alive_pkm_player0: list, alive_pkm_player1: list)
    '''
    # Reset the environment to get the initial state
    state, _ = env.reset()
    env.render(mode)

    # Perform a single battle until it's terminated
    terminated = False
    moves_counter = 0
    while not terminated:
        my_action = player0.get_action(state[0])
        opp_action = player1.get_action(state[1])
        state, _, terminated, _, _ = env.step([my_action,opp_action])
        moves_counter += 1
    
    # Return the winner player of the battle
    return moves_counter, env


def main():

    # Perform "n_battles" battles
    enable_print = False
    n_battles = 100
    avg_moves = 0
    winner_pkm_team: PkmTeam = None
    env: PkmBattleEnv = None
    win_rate_dict = {}
    for i in range(n_battles):
        # Choose random pokemons for both teams
        
        # Random initialization for each battle
        players = (RandomPlayer(), RandomPlayer())
        teams = (PkmTeam(), PkmTeam())
        # Create a Pokemon battle environment
        env = PkmBattleEnv(
            teams=teams,
            debug=False,
            encode=(players[0].requires_encode(), players[1].requires_encode())
        )
        # Run the battle which returns some statistics
        n_moves, env = run_statistics_battle(players[0], players[1], env)
        avg_moves += n_moves
        winner_pkm_team = teams[env.winner]
        for pkm in winner_pkm_team.party:
            print(f'{pkm.pkm_id}')
            if pkm.pkm_id not in win_rate_dict.keys():
                win_rate_dict[pkm.pkm_id] = 0
            win_rate_dict[pkm.pkm_id] += 1
        # Case of print of results
        if enable_print:
            print(f'Battle {i+1}:')
            print(f'Number of moves: {n_moves} moves.')
            print(f'Winner team: ')
            for pkm in winner_pkm_team.party:
                print(f'\t- {pkm.pkm_id}')
            
    avg_moves /= n_battles
    print(f'>>> Average number of moves per battle: {avg_moves}')
    print(f'>>> Pokemon win rate:\n{dict(sorted(win_rate_dict.items(), key=lambda item: item[1], reverse=True))}')
    
    players[0].close()
    return


if __name__ == '__main__':
    main()