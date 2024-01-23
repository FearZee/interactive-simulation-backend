import math


def calculate_solar_angle(time, day=1):
    # Formula to calculate solar declination angle
    declination = 23.45 * math.sin(math.radians((360 / 365) * (day - 81)))

    # Hour angle calculation
    hour_angle = 15 * (time - 12)

    # Solar zenith angle calculation
    solar_zenith_angle = math.degrees(
        math.acos(
            math.sin(math.radians(declination)) * math.sin(math.radians(52))
            + math.cos(math.radians(declination))
            * math.cos(math.radians(52))
            * math.cos(math.radians(hour_angle))
        )
    )

    # Solar elevation angle
    solar_elevation_angle = 90 - solar_zenith_angle

    return solar_elevation_angle
