# API-Football – Formats de réponses attendus (synthèse)

Les réponses renvoient généralement `errors`, `results`, `paging`, puis `response`. Ci-dessous, les champs clés utiles par endpoint (sans exemples complets).

## Référentiels
- `/countries` : liste d’objets `{name, code, flag}`.
- `/leagues` : chaque entrée contient `{league: {id, name, type, logo}, country: {name, code, flag}, seasons: [{year, start, end, current, coverage: {fixtures{events,lineups,statistics_fixtures,statistics_players}, standings, players, top_scorers, top_assists, top_cards, injuries, predictions, odds}}]}`.
- `/leagues/seasons` : tableau d’années.
- `/timezone` : tableau de chaînes timezone.

## Équipes
- `/teams` : objets `{team: {id, name, code, country, founded, national, logo}, venue: {id, name, address, city, capacity, surface, image}}`.
- `/teams/countries` : `{name, code, flag}`.
- `/teams/seasons` : tableau d’années.

## Stades
- `/venues` : `{id, name, address, city, country, capacity, surface, image}`.

## Classements
- `/standings` : `response` contient `{league: {id, name, country, season, standings: [[{rank, team{id,name,logo}, points, goalsDiff, form, status, description, all{played,win,draw,lose,goals{for,against}}, home, away, update}]]}}`.

## Fixtures (générique)
- `/fixtures` : objets `{fixture: {id, referee, timezone, date, timestamp, periods, venue{id,name,city}, status{long,short,elapsed,extra}}, league: {id,name,country,logo,flag,season,round}, teams: {home{id,name,logo,winner}, away{...}}, goals{home,away}, score{halftime,fulltime,extratime,penalty}}`.
- `/fixtures/rounds` : tableau de libellés de journées.
- Statuts utilisables : voir mapping `match_status.txt` (codes short/long/type/description).

## Head-to-head
- `/fixtures/headtohead` : même structure qu’un `fixtures`, filtré sur les confrontations.

## Détails de match
- `/fixtures/events` : `{time{elapsed,extra}, team{id,name,logo}, player{id,name}, assist{id,name}, type, detail, comments}`.
- `/fixtures/lineups` : `{team{id,name,logo,colors}, formation, startXI[{player{id,name,number,pos,grid}}], substitutes[{player{...}}], coach{id,name,photo}}`.
- `/fixtures/statistics` : `{team{id,name,logo}, statistics: [{type, value}]}` (value numérique ou pourcentage string).
- `/fixtures/players` : `{team{id,name,logo,update}, players: [{player{id,name,photo}, statistics: [{games{minutes,number,position,rating,captain,substitute}, shots, goals{total,conceded,assists,saves}, passes{total,key,accuracy}, dribbles, fouls, cards, penalty...}]}]}`.

## Joueurs
- `/players` : `player` bloc bio + `statistics` (team, league, games, substitutes, shots, goals, passes, tackles, duels, dribbles, fouls, cards, penalty).
- `/players/seasons` : tableau d’années (global ou pour un joueur).
- `/players/squads` : `{team{id,name,logo}, players[{id,name,age,number,position,photo}]}`.
- `/players/profiles` : `{player: {id, name, firstname, lastname, age, birth{date,place,country}, nationality, height, weight, number, position, photo}}`.
- `/players/teams` : liste `{team{id,name,logo}, seasons: [years...]}`.

## Tops joueurs
- `/players/topscorers`, `/topassists`, `/topyellowcards`, `/topredcards` : mêmes champs que `/players` (bio + bloc statistics), ordonnés par métrique (buts, assists, jaunes, rouges).

## Blessures / indisponibilités
- `/injuries` : `{player{id,name,photo,type,reason}, team{id,name,logo}, fixture{id,timezone,date,timestamp}, league{id,season,name,country,logo,flag}}`.
- `/sidelined` : liste d’entrées `{type, start, end}` pour un player/coach.

## Pronostics & cotes
- `/predictions` : `{predictions:{winner{id,name,comment}, win_or_draw, under_over, goals{home,away}, advice, percent{home,draw,away}}, league{...}, teams{home{...last_5,league{form,fixtures,goals,biggest,clean_sheet,failed_to_score}}, away{...}}, comparison{form,att,def,poisson_distribution,h2h,goals,total}, h2h:[fixtures...]}`.
- `/odds` (par fixture ou date/league) : `{fixture{id}, league{id,name}, bookmakers:[{id,name,bets:[{id,name,values:[{value,odd,handicap?}]}]}]}`. Les sous-ressources `/odds/bookmakers`, `/odds/bets`, `/odds/mapping`, `/odds/live` renvoient les listes associées (ids, noms, champs handicaps/updates).

## Statistiques d’équipe
- `/teams/statistics` : `{league{id,name,country,logo,flag,season}, team{id,name,logo}, form, fixtures{played,wins,draws,loses}, goals{for{total,average,minute,under_over}, against{...}}, biggest{streak,wins,loses,goals}, clean_sheet, failed_to_score, penalty, lineups[{formation,played}], cards{yellow{...}, red{...}}}`.

## Transferts
- `/transfers` : `{player{id,name}, update, transfers:[{date, type, teams{in{id,name,logo}, out{id,name,logo}}}]}`.

## Palmarès
- `/trophies` : `{league, country, season, place}` pour chaque trophée (player ou coach).

## Coachs
- `/coachs` : `{id,name,firstname,lastname,age,birth{date,place,country}, nationality, height, weight, photo, team{id,name,logo}, career:[{team{id,name,logo}, start, end}]}`.

## Divers
- `/status` : statut API, quota et informations de compte (champs selon abonnement).
