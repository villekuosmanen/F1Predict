def getRetirementBlame(status):
    if status == "Collision":
        return (1, 0, 0)
    elif status == "Accident":
        return (1, 0, 0)
    elif status == "Engine":
        return (0, 0, 1)
    elif status == "Gearbox":
        return (0, 1, 0)
    elif status == "Hydraulics":
        return (0, 1, 0)
    elif status == "Brakes":
        return (0, 1, 0)
    elif status == "Spun off":
        return (1, 0, 0)
    elif status == "Suspension":
        return (0, 1, 0)
    elif status == "Electrical":
        return (0, 0.5, 0.5)
    elif status == "Power Unit":
        return (0, 0, 1)
    elif status == "Collision damage":
        return (1, 0, 0)
    elif status == "Wheel":
        return (0, 1, 0)
    elif status == "Transmission":
        return (0, 1, 0)
    elif status == "Mechanical":
        return (0, 0.5, 0.5)
    elif status == "Puncture":
        return (0.667, 0.333, 0)
    elif status == "Driveshaft":
        return (0, 1, 0)
    elif status == "Oil leak":
        return (0, 0.5, 0.5)
    elif status == "Tyre":
        return (0, 1, 0)
    elif status == "Fuel pressure":
        return (0, 0.5, 0.5)
    elif status == "Clutch":
        return (0, 1, 0)
    elif status == "Electronics":
        return (0, 0.5, 0.5)
    elif status == "Power loss":
        return (0, 0, 1)
    elif status == "Overheating":
        return (0, 0.5, 0.5)
    elif status == "Throttle":
        return (0, 1, 0)
    elif status == "Wheel nut":
        return (0, 1, 0)
    elif status == "Exhaust":
        return (0, 1, 0)
    elif status == "Steering":
        return (0, 1, 0)
    elif status == "Fuel system":
        return (0, 0.5, 0.5)
    elif status == "Water leak":
        return (0, 1, 0)
    elif status == "Battery":
        return (0, 0, 1)
    elif status == "ERS":
        return (0, 0, 1)
    elif status == "Water pressure":
        return (0, 1, 0)
    elif status == "Rear wing":
        return (0.667, 0.333, 0)
    elif status == "Vibrations":
        return (0.667, 0.333, 0)
    elif status == "Technical":
        return (0, 0.5, 0.5)
    elif status == "Oil pressure":
        return (0, 0.5, 0.5)
    elif status == "Pneumatics":
        return (0, 1, 0)
    elif status == "Turbo":
        return (0, 0, 1)
    elif status == "Front wing":
        return (0.667, 0.333, 0)
    return (0.334, 0.333, 0.333)