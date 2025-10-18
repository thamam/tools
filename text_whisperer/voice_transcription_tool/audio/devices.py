"""
audio/devices.py - Audio device management for the Voice Transcription Tool.

Provides audio input device discovery, selection, and testing capabilities
through PyAudio device enumeration.
"""

import logging
from typing import List, Dict, Any, Optional

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


class AudioDeviceManager:
    """Manages audio input devices."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.devices = []
        self._refresh_devices()
    
    def _refresh_devices(self) -> None:
        """Refresh the list of available audio devices."""
        self.devices.clear()
        
        if PYAUDIO_AVAILABLE:
            try:
                audio = pyaudio.PyAudio()
                device_count = audio.get_device_count()
                
                for i in range(device_count):
                    device_info = audio.get_device_info_by_index(i)
                    if device_info['maxInputChannels'] > 0:  # Input device
                        self.devices.append({
                            'index': i,
                            'name': device_info['name'],
                            'channels': device_info['maxInputChannels'],
                            'sample_rate': device_info['defaultSampleRate'],
                            'api': device_info.get('hostApi', 'Unknown')
                        })
                
                audio.terminate()
                self.logger.info(f"Found {len(self.devices)} audio input devices")
                
            except Exception as e:
                self.logger.error(f"Failed to enumerate audio devices: {e}")
        else:
            self.logger.warning("PyAudio not available - cannot enumerate devices")
    
    def get_devices(self) -> List[Dict[str, Any]]:
        """Get list of available audio input devices."""
        return self.devices.copy()
    
    def get_devices_info(self) -> List[str]:
        """Get formatted device information for display."""
        info = []
        if self.devices:
            for device in self.devices:
                info.append(f"📱 Device {device['index']}: {device['name']} "
                           f"(Channels: {device['channels']}, "
                           f"Rate: {device['sample_rate']:.0f}Hz)")
        else:
            info.append("⚠️ No audio devices detected")
        
        return info
    
    def get_default_device(self) -> Dict[str, Any]:
        """Get the default audio input device."""
        if PYAUDIO_AVAILABLE:
            try:
                audio = pyaudio.PyAudio()
                default_info = audio.get_default_input_device_info()
                audio.terminate()
                
                return {
                    'index': default_info['index'],
                    'name': default_info['name'],
                    'channels': default_info['maxInputChannels'],
                    'sample_rate': default_info['defaultSampleRate'],
                    'api': default_info.get('hostApi', 'Unknown')
                }
            except Exception as e:
                self.logger.error(f"Failed to get default device: {e}")
        
        # Fallback
        return {
            'index': 0,
            'name': 'System Default',
            'channels': 1,
            'sample_rate': 16000,
            'api': 'System'
        }
    
    def get_device_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get device information by name."""
        for device in self.devices:
            if name.lower() in device['name'].lower():
                return device
        return None
    
    def get_device_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Get device information by index."""
        for device in self.devices:
            if device['index'] == index:
                return device
        return None
    
    def test_device(self, device_index: int) -> bool:
        """Test if a specific device is working."""
        if not PYAUDIO_AVAILABLE:
            return True  # Assume system devices work
        
        try:
            audio = pyaudio.PyAudio()
            
            # Try to open the device
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=1024
            )
            
            # Read a small amount of data
            data = stream.read(1024, exception_on_overflow=False)
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            return len(data) > 0
            
        except Exception as e:
            self.logger.error(f"Device test failed for index {device_index}: {e}")
            return False
    
    def refresh(self) -> None:
        """Refresh the device list."""
        self._refresh_devices()
    
    def get_device_count(self) -> int:
        """Get the number of available devices."""
        return len(self.devices)


if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from utils.logger import setup_logging
    
    setup_logging()
    
    # Test device manager
    device_manager = AudioDeviceManager()
    
    print(f"Device count: {device_manager.get_device_count()}")
    
    devices = device_manager.get_devices()
    print(f"Devices found: {'✅' if devices else '❌'}")
    
    device_info = device_manager.get_devices_info()
    print("Device info:")
    for info in device_info:
        print(f"  {info}")
    
    default_device = device_manager.get_default_device()
    print(f"Default device: {default_device['name']}")
    
    print("✅ Audio devices module test completed!")
