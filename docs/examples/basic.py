from configmanager import ConfigManager, ConfigItem

config = ConfigManager(
    ConfigItem('uploads', 'tmp_dir', default='/tmp/uploads'),
    ConfigItem('uploads', 'threads', default=3, type=int),
    ConfigItem('uploads', 'enabled', default=False, type=bool),
)

uploads_enabled = config.uploads.enabled
uploads_threads = config.uploads.threads

print(uploads_enabled.value)  # False
print(uploads_enabled.has_value)  # False

uploads_enabled.value = True
print(uploads_enabled.value)  # True

print(uploads_enabled.default)  # False
print(uploads_enabled.has_value)  # False

uploads_threads.value = 5
print(uploads_threads.value)  # 5

uploads_threads.reset()
print(uploads_threads.value)  # 3

print(uploads_threads.name)  # 'uploads.threads'

print(uploads_threads.path)  # ('uploads', 'threads')
