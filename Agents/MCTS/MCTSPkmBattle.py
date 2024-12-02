from vgc.behaviour.MCTSBattlePolicies import MCTSPlayer
from vgc.datatypes.Objects import PkmTeam
from vgc.engine.PkmBattleEnv import PkmBattleEnv


def run_battle(player0: MCTSPlayer, player1: MCTSPlayer, env: PkmBattleEnv, mode='console') -> PkmTeam:
    '''
    Performs a single battle between two players and their teams in the environment passed as parameter.
    '''
    # Reset the environment to get the initial state
    env.reset()
    env.render(mode)
    state, _, _, _, _ = env.__get_states()
    # Perform a single battle until it's terminated
    terminated = False
    while not terminated:
        my_action = player0.get_action(state[0])
        opp_action = player1.get_action(state[1])
        state, _, terminated, _, _ = env.step([my_action,opp_action])
    # Return the winner player of the battle
    if state.teams[0].fainted():
        return state.teams[0]
    if state.teams[1].fainted():
        return state.teams[1]
    return None


def main():
    # Create 2 players which perform the Monte Carlo Tree Search (and the 2 teams for the battle)
    player0 = MCTSPlayer()
    player1 = MCTSPlayer()
    team0 = PkmTeam()
    team1 = PkmTeam()
    # Create a Pokemon battle environment and reset it to default settings
    env = PkmBattleEnv(
        teams=(team0,team1),
        debug=True,
        encode=(player0.requires_encode(), player1.requires_encode())
    )
    # Perform "n_battles" battles
    n_battles = 3
    for i in range(n_battles):
        print(f'\n\n\n==================================== Battle {i+1} ====================================\n')
        winner_player = run_battle(player0, player1, env)
        print(f'Player {winner_player} won the battle!')
    return


if __name__ == '__main__':
    main()
