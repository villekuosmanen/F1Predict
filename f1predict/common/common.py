def getColor(constructor):
    return {
        "Mercedes": "#00D2BE",
        "Ferrari": "#DC0000",
        "Red Bull": "#0600EF",
        "Aston Martin": "#006F62",
        "Williams": "#005AFF",
        "Alpine F1 Team": "#0090FF",
        "AlphaTauri": "#2B4562",
        "Haas F1 Team": "#FFFFFF",
        "McLaren": "#FF9800",
        "Alfa Romeo": "#900000"
    }.get(constructor, "#000000")

def getCurrentYear():
    return 2021