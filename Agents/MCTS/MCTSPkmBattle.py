from MCTSBattlePolicies import MCTSPlayer
from vgc.datatypes.Objects import PkmTeam, PkmFullTeam
from vgc.engine.PkmBattleEnv import PkmBattleEnv
from vgc.util.generator.PkmRosterGenerators import RandomPkmRosterGenerator
from vgc.util.generator.PkmTeamGenerators import RandomTeamFromRoster


def run_battle(player0: MCTSPlayer, player1: MCTSPlayer, env: PkmBattleEnv, mode='console') -> PkmTeam:
    '''
    Performs a single battle between two players and their teams in the environment passed as parameter.
    '''
    # Reset the environment to get the initial state
    env.reset()
    env.render(mode)
    # Perform a single battle until it's terminated
    terminated = False
    while not terminated:
        my_action = player0.get_action(env)
        opp_action = player1.get_action(env)
        states, _, terminated, _, _ = env.step([my_action,opp_action])
        env = states[0]
    # Return the winner player of the battle
    if env.teams[0].fainted():
        return env.teams[0]
    if env.teams[1].fainted():
        return env.teams[1]
    return None


def main():
    # Random pokemon roster and team generators
    pkm_roster = RandomPkmRosterGenerator().gen_roster()
    team_gen = RandomTeamFromRoster(roster=pkm_roster)
    # Create 2 players which perform the Monte Carlo Tree Search (and the 2 teams for the battle)
    player0 = MCTSPlayer('Player 0')
    player1 = MCTSPlayer('Player 1')
    full_team0: PkmFullTeam = team_gen.get_team()
    full_team1: PkmFullTeam = team_gen.get_team()
    team0 = full_team0.get_battle_team([0,1,2])
    team1 = full_team1.get_battle_team([0,1,2])
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
