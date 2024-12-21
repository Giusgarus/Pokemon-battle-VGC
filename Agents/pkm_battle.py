from copy import deepcopy
import sys
from vgc.behaviour.BattlePolicies import BattlePolicy
from vgc.datatypes.Objects import PkmFullTeam
from vgc.engine.PkmBattleEnv import PkmBattleEnv
from vgc.util.generator.PkmRosterGenerators import RandomPkmRosterGenerator
from vgc.util.generator.PkmTeamGenerators import RandomTeamFromRoster
from util import run_battle, get_params_combinations, write_metrics, get_agents, get_parameters_from_env


def main():
    overall_metrics_dict = {
        'winrate': 0,
        'avg_n_turns': 0,
        'avg_n_switches': 0,
        'avg_hp_residue': 0
    }

    # Load informations from arguments got by CLI
    agents = get_agents()
    if agents[0] is None or agents[1] is None: return
    params_space_p0, params_space_p1 = get_parameters_from_env()

    # Create 2 players based on the agents passed as CLI argument
    player0: BattlePolicy = agents[0]
    player1: BattlePolicy = agents[1]

    # Set the parameters for the players 1
    if params_space_p1 != {}:
        params_p1 = {}
        for key, values in params_space_p1.items():
            params_p1[key] = values[0]
        try:
            player1.set_parameters(params_p1)
        except:
            pass

    # Iterate on each parameters' combination
    combinations_list: list[dict] = get_params_combinations(params_space_p0)
    print(f'\n=== Total Combinations ===\n{len(combinations_list)}\n=== Number of battles per combination ===\n{combinations_list[0]["N_BATTLES"]}')
    for i, params in enumerate(combinations_list):
        if params_space_p0 != {}:
            try:
                player0.set_parameters(params)
            except:
                pass

        # Perform "N_BATTLES" battles
        player0_winrate = 0
        print(f'\n=== Combination ===\n{i+1}/{len(combinations_list)}\n=== Parameters ===\n{params}\nBattles:')
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
            # Run the battle
            metrics_dict = run_battle(player0, player1, env, mode='no_output')
            if metrics_dict['winner'] == 0:
                player0_winrate += 1
            print(f'>>> Battle {j+1}/{params["N_BATTLES"]}: player 0 winrate = {player0_winrate}/{j+1} ({(player0_winrate/(j+1))*100:.2f}%)')
            # Update the metrics dictionary based on the battle done
            overall_metrics_dict['avg_n_turns'] += metrics_dict['n_turns']
            overall_metrics_dict['avg_n_switches'] += metrics_dict['n_switches']
            overall_metrics_dict['avg_hp_residue'] += metrics_dict['hp_residue']
            # Reset the environment
            env.reset()
            player0.n_switches = 0
        # Compute the average of the metrics
        overall_metrics_dict['avg_n_turns'] = round(number=(overall_metrics_dict['avg_n_turns']/params['N_BATTLES']), ndigits=2)
        overall_metrics_dict['avg_n_switches'] = round(number=(overall_metrics_dict['avg_n_switches']/params['N_BATTLES']), ndigits=2)
        overall_metrics_dict['avg_hp_residue'] = round(number=(overall_metrics_dict['avg_hp_residue']/params['N_BATTLES']), ndigits=2)
        overall_metrics_dict['winrate'] = round(number=(player0_winrate/params['N_BATTLES'])*100, ndigits=2)
        # Print and save metrics
        print(f'\n=== Parameters ===\n{params}\n=== Winrate ===\n{overall_metrics_dict["winrate"]}%')
        write_metrics(
            metrics_dict=overall_metrics_dict,
            params=params
        )
        # Reset metrics
        overall_metrics_dict['avg_n_turns'] = 0
        overall_metrics_dict['avg_n_switches'] = 0
        overall_metrics_dict['avg_hp_residue'] = 0
        overall_metrics_dict['winrate'] = 0
    return


if __name__ == '__main__':
    main()
