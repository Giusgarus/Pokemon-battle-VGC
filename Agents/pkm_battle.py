from copy import deepcopy
from vgc.behaviour.BattlePolicies import BattlePolicy
from vgc.datatypes.Objects import PkmFullTeam
from vgc.engine.PkmBattleEnv import PkmBattleEnv
from vgc.util.generator.PkmRosterGenerators import RandomPkmRosterGenerator
from vgc.util.generator.PkmTeamGenerators import RandomTeamFromRoster
from util import run_battle, get_params_combinations, write_statistics, get_agents, load_env, get_parameters_from_env


def main():
    # Load informations from arguments got by CLI
    agents = get_agents()
    if agents[0] is None or agents[1] is None: return
    if not load_env(): return
    params_space = get_parameters_from_env()
    # Create 2 players which perform the Monte Carlo Tree Search (and the 2 teams for the battle)
    player0: BattlePolicy = agents[0]
    player1: BattlePolicy = agents[1]
    # Execute N_BATTLES for each parameters combination
    for i, params in enumerate(get_params_combinations(params_space)):
        player0.set_parameters(params)
        # Perform "n_battles" battles
        player0_winrate = 0
        for j in range(params['N_BATTLES']):
            # Random pokemon roster and team generators
            pkm_roster = RandomPkmRosterGenerator().gen_roster()
            team_gen = RandomTeamFromRoster(roster=pkm_roster)
            # Generate a random team for both players
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
            print(f'\n\n\n==================================== Battle {j+1} ====================================\n')
            winner_player = run_battle(player0, player1, env, mode='no_output')
            print(f'Player 0 won {player0_winrate}/{j+1} battles ({(player0_winrate/(j+1))*100:.2f}%)')
            if winner_player == 0:
                player0_winrate += 1
            env.reset()
        print(f'\n\nPlayer 0 winrate: {player0_winrate}/{params["N_BATTLES"]} = {player0_winrate/params["N_BATTLES"]*100:.2f}%\n')
        write_statistics(
            statistics_string=f'\n\nWinrate: {player0_winrate}/{params["N_BATTLES"]} = {player0_winrate/params["N_BATTLES"]*100:.2f}%\n',
            params=params,
            mode='w' if i == 0 else 'a'
        )
    return


if __name__ == '__main__':
    main()
