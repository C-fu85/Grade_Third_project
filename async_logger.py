import sys
import queue
from threading import Thread, Event
from datetime import datetime
import io

class async_logger:
    def __init__(self, filepath, buffer_size=5000):  # Increased buffer size
        self.terminal = sys.stdout
        self.filepath = filepath
        self.buffer_size = buffer_size
        self.buffer = queue.Queue(maxsize=buffer_size)
        # Using StringIO for in-memory buffering
        self.memory_buffer = io.StringIO()
        self.memory_buffer_size = 0
        self.memory_buffer_limit = 1024 * 512  # 512KB in-memory buffer
        self.log_file = open(filepath, "w", encoding="utf-8", buffering=1024 * 1024)  # 1MB buffer
        self.exit_flag = Event()
        self.flush_counter = 0
        
        # Start background thread for writing to file
        self.writer_thread = Thread(target=self._background_writer, daemon=True)
        self.writer_thread.start()

    def _background_writer(self):
        while not self.exit_flag.is_set() or not self.buffer.empty():
            try:
                messages = []
                # Try to get multiple messages at once - increased batch size
                for _ in range(min(500, self.buffer.qsize())):
                    try:
                        message = self.buffer.get_nowait()
                        messages.append(message)
                    except queue.Empty:
                        break
                
                if messages:
                    joined_messages = ''.join(messages)
                    self.memory_buffer.write(joined_messages)
                    self.memory_buffer_size += len(joined_messages)
                    
                    # Flush memory buffer to file if it exceeds limit
                    if self.memory_buffer_size >= self.memory_buffer_limit:
                        self.log_file.write(self.memory_buffer.getvalue())
                        self.log_file.flush()
                        self.memory_buffer = io.StringIO()
                        self.memory_buffer_size = 0
                    
                    for _ in messages:
                        self.buffer.task_done()
                else:
                    # If memory buffer has content but no new messages, flush it
                    if self.memory_buffer_size > 0:
                        self.log_file.write(self.memory_buffer.getvalue())
                        self.log_file.flush()
                        self.memory_buffer = io.StringIO()
                        self.memory_buffer_size = 0
                    self.exit_flag.wait(timeout=0.1)
                    
            except Exception as e:
                print(f"Error in background writer: {e}", file=self.terminal)

    def write(self, message):
        try:
            self.terminal.write(message)
            self.buffer.put(message)
            
            self.flush_counter += 1
            if self.flush_counter >= self.buffer_size:
                self.flush()
                self.flush_counter = 0
        except Exception as e:
            print(f"Error in write: {e}", file=self.terminal)

    def flush(self):
        self.terminal.flush()
        if self.memory_buffer_size > 0:
            self.log_file.write(self.memory_buffer.getvalue())
            self.log_file.flush()
            self.memory_buffer = io.StringIO()
            self.memory_buffer_size = 0

    def close(self):
        self.flush()
        self.exit_flag.set()
        self.writer_thread.join()
        self.memory_buffer.close()
        self.log_file.close()

    def __del__(self):
        self.close()