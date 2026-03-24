export const getDistanceInMeters = (origin, destination) => {
    const toRadians = (degrees) => (degrees * Math.PI) / 180;

    const EARTH_RADIUS_METERS = 6371000;


    const originLatRadians = toRadians(origin.lat);
    const destinationLatRadians = toRadians(destination.lat);

    const latDiffRadians = toRadians(destination.lat - origin.lat);
    const lonDiffRadians = toRadians(destination.lon - origin.lon);

    const halfChordLengthSquare =
        Math.sin(latDiffRadians / 2) * Math.sin(latDiffRadians / 2) +
        Math.cos(originLatRadians) * Math.cos(destinationLatRadians) *
        Math.sin(lonDiffRadians / 2) * Math.sin(lonDiffRadians / 2);

    const angularDistanceRadians = 2 * Math.atan2(
        Math.sqrt(halfChordLengthSquare),
        Math.sqrt(1 - halfChordLengthSquare)
    );

    const distanceInMeters = EARTH_RADIUS_METERS * angularDistanceRadians;

    return distanceInMeters;
};