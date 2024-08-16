export default function getDeviceId() {
    let deviceId = localStorage.getItem('device_id');
    if (!deviceId) {
        deviceId = 'device-' + Math.random().toString(36).substr(2, 16);
        localStorage.setItem('device_id', deviceId);
        console.log('New Device ID generated and saved:', deviceId);
    } else {
        console.log('Existing Device ID:', deviceId);
    }
    return deviceId;
}
