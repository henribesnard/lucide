# Structure d'Analyse de Match
## Guide complet pour l'analyse des paris sportifs

---

## 1. Flux de données et endpoints

① predictions?fixture={id}  
② fixtures/headtohead?h2h={team1}-{team2}  
③ Pour chaque fixture du H2H :
- fixtures/statistics?fixture={id}
- fixtures/players?fixture={id}
- fixtures/events?fixture={id}
- fixtures/lineups?fixture={id}

---

## 2. Structure de données par type de pari

### 2.1 Pari 1X2

| Source | Données | Utilisation |
|--------|---------|-------------|
| predictions | form | Série W/D/L |
| predictions | fixtures wins/draws/loses | Bilan |
| predictions | comparison | % |
| h2h | scores | Historique |
| standings | rank, points | Classement |

**Indicateurs clés**
- Forme récente
- Performance domicile/extérieur
- Historique H2H
- Écart classement
- Séries en cours

---

### 2.2 Pari Nombre de buts (Over/Under)

Sources : predictions, h2h  
Indicateurs :
- Moyenne buts
- % Over 2.5
- Clean sheets
- BTTS
- Score H2H

---

### 2.3 Pari Tirs

Sources : fixtures/statistics, fixtures/players  
Indicateurs :
- Moyenne tirs
- Ratio cadrés
- Top shooters
- % tirs surface

---

### 2.4 Pari Corners

Sources : fixtures/statistics  
Indicateurs :
- Moyenne corners
- Total H2H
- Corrélation possession
- Style de jeu

---

### 2.5 Pari Cartons

Sources : fixtures/statistics, fixtures/events, fixtures/players, players  
Indicateurs :
- Moyenne cartons
- Joueurs sanctionnés
- Arbitre
- Ratio fautes/cartons
- Tension H2H

---

### 2.6 Pari Carton Joueur

Sources : players, fixtures/events, players games  
Indicateurs :
- Cartons / 90 min
- Position
- Fautes / match
- Cartons H2H
- Titularisation

---

### 2.7 Pari Buteurs

Sources : fixtures/events, players, fixtures/players  
Indicateurs :
- Buts / 90 min
- Tirs / 90 min
- Conversion
- Pénalty
- H2H
- Forme récente

---

### 2.8 Pari Passeurs

Sources : fixtures/events, players, fixtures/players  
Indicateurs :
- Assists / 90 min
- Passes clés
- Position
- Combinaisons
- Historique H2H

---

## 3. Structure JSON recommandée

```json
{
  "match_info": {},
  "form_analysis": {},
  "goals_analysis": {},
  "shots_analysis": {},
  "corners_analysis": {},
  "cards_analysis": {},
  "scorers_analysis": {},
  "assisters_analysis": {},
  "h2h_summary": {}
}
