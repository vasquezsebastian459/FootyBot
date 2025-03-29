import pickle

# Load embeddings from the pkl file
with open('chat_bot/embedding/open_ai_embeddings/all_tables_embedding_large.pkl', 'rb') as f:
    embeddings = pickle.load(f)
    # keys = embeddings.keys()
    # for key in keys:
    #     print(key)
embeddings_to_remove = [
    'public.affected_rows',
    'public.agg_min_max_petal_field_position',
    'public.t_defense_min_max',
    'public.t_field_player_min_max',
    'public.t_forward_min_max',
    'public.t_fullback_min_max',
    'public.t_goalkeeper_min_max',
    'public.t_midfielder_min_max',
    'public.t_team_defensive_min_max',
    'public.t_team_offensive_min_max',
    'public.t_team_style_min_max',
    'public.t_wingback_min_max',
    'public.t_winger_min_max',
    'public.agg_xg_zone',
    'public.agg_xt_matrix',
    'public.agg_xt_xy',
    'public.agg_xt_zone',
    'public.delete_match',
    'public.det_match_tracking',
    'public.dim_tracking_status',
    'public.det_shot',
    'public.dim_dallas_position',
    'public.dim_field_color',
    'public.dim_login_type',
    'public.dim_match_status_ks',
    'public.dim_match_status',
    'public.dim_provider',
    'public.dim_score',
    'public.dim_server',
    'public.dim_shot_detection_status',
    'public.dim_source',
    'public.fac_game_clip',
    'public.fac_team_fifa',
    'public.fac_tm_summary',
    'public.v_player_notm' ,
    'public.v_team_game_metric',
    'public.t_keeper_sweeper',
    'public.t_smother',
    'public.t_season_fm_player',
    'public.v_player_sc',
    'v_player_wrong_gender'
]

# Filter out embeddings you want to keep
filtered_embeddings = {key: value for key, value in embeddings.items() if key not in embeddings_to_remove}
# Save the filtered embeddings to a new pickle file
with open('chat_bot/embedding/open_ai_embeddings/reduced_tables_embeddings.pkl', 'wb') as f:
    pickle.dump(filtered_embeddings, f)

print(f"Original number of tables: {len(embeddings)}")
print(f"Number of tables after removal: {len(filtered_embeddings)}")