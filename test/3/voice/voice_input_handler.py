# файл: voice/voice_input_handler.py
import pyaudio
import json
import threading
import queue
import time
from vosk import Model, KaldiRecognizer

class VoiceInputHandler:
    """Обработчик голосового ввода с использованием Vosk"""
    
    def __init__(self, model_path):
        """
        Инициализация обработчика голосового ввода
        
        Args:
            model_path (str): Путь к модели Vosk
        """
        self.model_path = model_path
        self.model = None
        self.recognizer = None
        self.audio = None
        self.stream = None
        self.is_listening = False
        self.should_stop = False
        self.audio_queue = queue.Queue()
        self.recognition_lock = threading.Lock()
        self.current_recognition = None
        
        # Инициализация Vosk модели
        try:
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, 16000)
            print("Vosk модель успешно загружена")
        except Exception as e:
            print(f"Ошибка загрузки модели Vosk: {e}")
            raise
    
    def start_listening(self):
        """Запуск потока захвата из микрофона"""
        with self.recognition_lock:
            if self.is_listening:
                return
            
            try:
                self.audio = pyaudio.PyAudio()
                self.stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=4000,
                    stream_callback=self._audio_callback
                )
                self.stream.start_stream()
                self.is_listening = True
                self.should_stop = False
                print("Начало прослушивания...")
            except Exception as e:
                print(f"Ошибка при запуске аудиопотока: {e}")
                self.is_listening = False
                raise
    
    def stop_listening(self):
        """Остановка захвата из микрофона"""
        with self.recognition_lock:
            if not self.is_listening:
                return
            
            self.should_stop = True
            
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            if self.audio:
                self.audio.terminate()
                self.audio = None
            
            self.is_listening = False
            print("Прослушивание остановлено")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Колбэк для получения аудиоданных от pyaudio"""
        if not self.should_stop:
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)
    
    def recognize_speech(self) -> str:
        """
        Распознавание речи из микрофона с возможностью досрочной остановки
        
        Returns:
            str: Распознанный текст или сообщение об ошибке
        """
        if not self.model:
            return "Модель не загружена"
        
        with self.recognition_lock:
            # Если уже идет распознавание, останавливаем его
            if self.is_listening:
                self.stop_listening()
                return "Распознавание отменено"
        
        try:
            self.start_listening()
            
            # Собираем аудиоданные
            audio_data = b''
            silent_chunks = 0
            max_silent_chunks = 20  # около 2 секунд тишины
            min_audio_chunks = 10    # минимум 1 секунда аудио
            max_chunks = 200  # максимум 10 секунд записи (200 * 0.05 сек)
            
            print("Говорите... (скажите что-нибудь)")
            
            for i in range(max_chunks):
                # Проверяем, не нужно ли остановиться
                if self.should_stop:
                    self.stop_listening()
                    return "Распознавание отменено пользователем"
                
                try:
                    chunk = self.audio_queue.get(timeout=0.05)
                    audio_data += chunk
                    
                    # Проверяем уровень звука
                    if len(chunk) > 0:
                        import struct
                        samples = struct.unpack('<' + 'h' * (len(chunk) // 2), chunk)
                        max_amplitude = max(abs(s) for s in samples) if samples else 0
                        
                        if max_amplitude < 500:  # Порог тишины
                            silent_chunks += 1
                        else:
                            silent_chunks = 0
                    
                    # Если достаточно тишины после речи, прекращаем запись
                    if silent_chunks > max_silent_chunks and len(audio_data) > min_audio_chunks * 4000:
                        break
                        
                except queue.Empty:
                    # Если нет данных в очереди и уже есть аудио, возможно, речь закончилась
                    if len(audio_data) > min_audio_chunks * 4000:
                        break
            
            self.stop_listening()
            
            if len(audio_data) < 4000:  # Меньше 0.25 секунды
                return "Не распознано"
            
            # Распознаем собранные аудиоданные
            if self.recognizer.AcceptWaveform(audio_data):
                result = json.loads(self.recognizer.Result())
                text = result.get('text', '')
                if text:
                    print(f"Распознано: {text}")
                    return text
                else:
                    return "Не распознано"
            else:
                # Проверяем частичный результат
                partial = json.loads(self.recognizer.PartialResult())
                partial_text = partial.get('partial', '')
                if partial_text:
                    print(f"Частичное распознавание: {partial_text}")
                    return partial_text
                return "Не распознано"
                
        except Exception as e:
            print(f"Ошибка распознавания: {e}")
            self.stop_listening()
            return "Не распознано"
