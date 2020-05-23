# audio_date_formatter

Loops over dirs and files and symlink to latest broadcast.

Before:

```
├── audio
│   ├── backup
│   │   ├── 20200104-backup.mp3
│   └── programa1
│       ├── 20200104-programa1.mp3
```

After executing 'audio_date_formatter.py':

```
├── audio
│   ├── backup
│   │   ├── 20200104-backup.mp3
│   │   └── backup.ogg -> 20200104-backup.mp3
│   └── programa1
│       ├── 20200104-programa1.mp3
│       └── programa1.ogg -> 20200104-programa1.mp3
```

# Intallation

1. Install packages:

```
sudo apt-get install ffmpeg lsof
```

2. Install python packages

```
pip3 install -r requirements.txt
```

# Configuration

1. Copy provided example configuration file:

```
cp config.sample config
```

2. Customize it with path to your audio directories, log, etc.

# Execution

```
python3 audio_date_formatter.py
```
