function processLinks(response, linksInfo) {
    // Flatten all positions into a single array to sort and process without conflict
    const replacements = [];

    // Iterate over each entity type in linksInfo
    Object.keys(linksInfo).forEach(entityType => {
        const entityData = linksInfo[entityType];
        // Iterate over each entity within the type
        Object.keys(entityData).forEach(entityKey => {
            const entityInfo = entityData[entityKey];
            const positions = entityInfo.positions;
            const link = entityInfo.link;
            // Collect all replacements
            positions.forEach(pos => {
                replacements.push({
                    start_pos: pos.start_pos,
                    end_pos: pos.end_pos,
                    entity: response.slice(pos.start_pos, pos.end_pos),
                    link: link
                });
            });
        });
    });

    // Sort replacements by start_pos in descending order
    replacements.sort((a, b) => b.start_pos - a.start_pos);

    // Apply replacements to the response string
    replacements.forEach(replacement => {
        response = response.slice(0, replacement.start_pos) + 
            `<a href="${replacement.link}" target="_blank">${replacement.entity}</a>` + 
            response.slice(replacement.end_pos);
    });

    return response;
}



// Example data to test the function
const linksInfo = {
    "players": {
        "Vinicius Junior": {
            "id": 1163220,
            "positions": [
                {
                    "start_pos": 40,
                    "end_pos": 55
                },
                {
                    "start_pos": 938,
                    "end_pos": 953
                }
            ],
            "link": "https://pro.driblab.com/player/1163220"
        }
    },
    "teams": {
        "Real Madrid": {
            "id": 4265,
            "positions": [
                {
                    "start_pos": 90,
                    "end_pos": 101
                },
                {
                    "start_pos": 125,
                    "end_pos": 136
                },
                {
                    "start_pos": 154,
                    "end_pos": 165
                },
                {
                    "start_pos": 189,
                    "end_pos": 200
                },
                {
                    "start_pos": 224,
                    "end_pos": 235
                },
                {
                    "start_pos": 255,
                    "end_pos": 266
                },
                {
                    "start_pos": 284,
                    "end_pos": 295
                },
                {
                    "start_pos": 313,
                    "end_pos": 324
                },
                {
                    "start_pos": 347,
                    "end_pos": 358
                },
                {
                    "start_pos": 384,
                    "end_pos": 395
                },
                {
                    "start_pos": 415,
                    "end_pos": 426
                },
                {
                    "start_pos": 450,
                    "end_pos": 461
                },
                {
                    "start_pos": 496,
                    "end_pos": 507
                },
                {
                    "start_pos": 515,
                    "end_pos": 526
                },
                {
                    "start_pos": 565,
                    "end_pos": 576
                },
                {
                    "start_pos": 584,
                    "end_pos": 595
                },
                {
                    "start_pos": 626,
                    "end_pos": 637
                },
                {
                    "start_pos": 645,
                    "end_pos": 656
                },
                {
                    "start_pos": 692,
                    "end_pos": 703
                },
                {
                    "start_pos": 727,
                    "end_pos": 738
                },
                {
                    "start_pos": 746,
                    "end_pos": 757
                },
                {
                    "start_pos": 798,
                    "end_pos": 809
                },
                {
                    "start_pos": 817,
                    "end_pos": 828
                },
                {
                    "start_pos": 845,
                    "end_pos": 856
                },
                {
                    "start_pos": 884,
                    "end_pos": 895
                }
            ],
            "link": "https://pro.driblab.com/team/4265"
        }
    },
    "seasons": {
        "ESP I 2023": {
            "id": 816527,
            "positions": [
                {
                    "start_pos": 65,
                    "end_pos": 75
                },
                {
                    "start_pos": 976,
                    "end_pos": 986
                }
            ],
            "link": "https://pro.driblab.com/league/1"
        }
    },
    "matches": {
        "Real Madrid vs UD Las Palmas": {
            "id": 549920,
            "positions": [
                {
                    "start_pos": 189,
                    "end_pos": 217
                }
            ],
            "link": "https://pro.driblab.com/game/549920"
        },
        "Real Madrid vs Osasuna": {
            "id": 549940,
            "positions": [
                {
                    "start_pos": 255,
                    "end_pos": 277
                }
            ],
            "link": "https://pro.driblab.com/game/549940"
        },
        "Real Madrid vs Rayo Vallecano": {
            "id": 549965,
            "positions": [
                {
                    "start_pos": 347,
                    "end_pos": 376
                }
            ],
            "link": "https://pro.driblab.com/game/549965"
        },
        "Real Madrid vs Valencia": {
            "id": 549978,
            "positions": [
                {
                    "start_pos": 384,
                    "end_pos": 407
                }
            ],
            "link": "https://pro.driblab.com/game/549978"
        },
        "Real Madrid vs RCD Mallorca": {
            "id": 550047,
            "positions": [
                {
                    "start_pos": 415,
                    "end_pos": 442
                }
            ],
            "link": "https://pro.driblab.com/game/550047"
        },
        "Real Madrid vs Almeria": {
            "id": 550063,
            "positions": [
                {
                    "start_pos": 125,
                    "end_pos": 147
                }
            ],
            "link": "https://pro.driblab.com/game/550063"
        },
        "UD Las Palmas vs Real Madrid": {
            "id": 550072,
            "positions": [
                {
                    "start_pos": 479,
                    "end_pos": 507
                }
            ],
            "link": "https://pro.driblab.com/game/550072"
        },
        "Real Madrid vs Girona FC": {
            "id": 550101,
            "positions": [
                {
                    "start_pos": 224,
                    "end_pos": 248
                },
                {
                    "start_pos": 515,
                    "end_pos": 539
                }
            ],
            "link": "https://pro.driblab.com/game/550101"
        },
        "Rayo Vallecano vs Real Madrid": {
            "id": 550106,
            "positions": [
                {
                    "start_pos": 547,
                    "end_pos": 576
                }
            ],
            "link": "https://pro.driblab.com/game/550106"
        },
        "Real Madrid vs Sevilla": {
            "id": 550117,
            "positions": [
                {
                    "start_pos": 284,
                    "end_pos": 306
                },
                {
                    "start_pos": 584,
                    "end_pos": 606
                }
            ],
            "link": "https://pro.driblab.com/game/550117"
        },
        "Valencia vs Real Madrid": {
            "id": 550130,
            "positions": [
                {
                    "start_pos": 614,
                    "end_pos": 637
                }
            ],
            "link": "https://pro.driblab.com/game/550130"
        },
        "Real Madrid vs Celta de Vigo": {
            "id": 550143,
            "positions": [
                {
                    "start_pos": 154,
                    "end_pos": 182
                },
                {
                    "start_pos": 645,
                    "end_pos": 673
                }
            ],
            "link": "https://pro.driblab.com/game/550143"
        },
        "Osasuna vs Real Madrid": {
            "id": 550147,
            "positions": [
                {
                    "start_pos": 681,
                    "end_pos": 703
                }
            ],
            "link": "https://pro.driblab.com/game/550147"
        },
        "RCD Mallorca vs Real Madrid": {
            "id": 550168,
            "positions": [
                {
                    "start_pos": 711,
                    "end_pos": 738
                }
            ],
            "link": "https://pro.driblab.com/game/550168"
        },
        "Real Madrid vs FC Barcelona": {
            "id": 550181,
            "positions": [
                {
                    "start_pos": 313,
                    "end_pos": 340
                },
                {
                    "start_pos": 746,
                    "end_pos": 773
                }
            ],
            "link": "https://pro.driblab.com/game/550181"
        },
        "Real Sociedad vs Real Madrid": {
            "id": 550196,
            "positions": [
                {
                    "start_pos": 781,
                    "end_pos": 809
                }
            ],
            "link": "https://pro.driblab.com/game/550196"
        },
        "Real Madrid vs Cadiz": {
            "id": 550204,
            "positions": [
                {
                    "start_pos": 817,
                    "end_pos": 837
                }
            ],
            "link": "https://pro.driblab.com/game/550204"
        },
        "Real Madrid vs Deportivo Alaves": {
            "id": 550229,
            "positions": [
                {
                    "start_pos": 845,
                    "end_pos": 876
                }
            ],
            "link": "https://pro.driblab.com/game/550229"
        },
        "Real Madrid vs Real Betis": {
            "id": 550248,
            "positions": [
                {
                    "start_pos": 884,
                    "end_pos": 909
                }
            ],
            "link": "https://pro.driblab.com/game/550248"
        }
    }
};

let response = "You should watch the following games of Vinicius Junior from the ESP I 2023 season:<br>1. Real Madrid vs Athletic Club<br>2. Real Madrid vs Almeria<br>3. Real Madrid vs Celta de Vigo<br>4. Real Madrid vs UD Las Palmas<br>5. Real Madrid vs Girona FC<br>6. Real Madrid vs Osasuna<br>7. Real Madrid vs Sevilla<br>8. Real Madrid vs FC Barcelona<br>9. Real Madrid vs Rayo Vallecano<br>10. Real Madrid vs Valencia<br>11. Real Madrid vs RCD Mallorca<br>12. Real Madrid vs Getafe<br>13. UD Las Palmas vs Real Madrid<br>14. Real Madrid vs Girona FC<br>15. Rayo Vallecano vs Real Madrid<br>16. Real Madrid vs Sevilla<br>17. Valencia vs Real Madrid<br>18. Real Madrid vs Celta de Vigo<br>19. Osasuna vs Real Madrid<br>20. RCD Mallorca vs Real Madrid<br>21. Real Madrid vs FC Barcelona<br>22. Real Sociedad vs Real Madrid<br>23. Real Madrid vs Cadiz<br>24. Real Madrid vs Deportivo Alaves<br>25. Real Madrid vs Real Betis<br><br>These games showcase Vinicius Junior's performances in the ESP I 2023 season, highlighting various statistics such as minutes played, distance covered, sprints, accelerations, and more.";

response = processLinks(response, linksInfo);
console.log(response);