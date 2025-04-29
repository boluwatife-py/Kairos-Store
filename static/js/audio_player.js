let currentAudio = null;
let currentBeatId = null;
let isPlaying = false;
let isRepeat = false;
let volume = 0.8; // Default volume
let isSeeking = false;
let currentPlaylist = []; // Array to store current playlist
let currentIndex = -1; // Current index in playlist

// Function to play a beat sample
function playSample(beatId, sampleUrl) {
    try {
        // If clicking the same beat that's currently playing, toggle play/pause
        if (currentBeatId === beatId) {
            if (isPlaying) {
                currentAudio.pause();
                isPlaying = false;
                updatePlayButton(beatId, false);
                updatePlayerPlayButton(false);
            } else {
                currentAudio.play().catch(error => {
                    console.error('Error playing audio:', error);
                    handlePlayError(error, beatId);
                });
                isPlaying = true;
                updatePlayButton(beatId, true);
                updatePlayerPlayButton(true);
            }
            return;
        }

        // If there's a different beat playing, stop it
        if (currentAudio) {
            currentAudio.pause();
            updatePlayButton(currentBeatId, false);
        }

        // Create and play new audio
        currentAudio = new Audio(sampleUrl);
        currentAudio.volume = volume;
        currentBeatId = beatId;
        isPlaying = true;

        // Update playlist and current index
        updatePlaylist(beatId);

        // Set up audio event listeners
        currentAudio.addEventListener('play', () => {
            updatePlayButton(beatId, true);
            updatePlayerPlayButton(true);
            showAudioPlayer(beatId);
            startEqualizer(beatId);
            updateNavigationButtons();
        });

        currentAudio.addEventListener('pause', () => {
            updatePlayButton(beatId, false);
            updatePlayerPlayButton(false);
            stopEqualizer(beatId);
        });

        currentAudio.addEventListener('ended', () => {
            if (isRepeat) {
                currentAudio.currentTime = 0;
                currentAudio.play().catch(error => {
                    console.error('Error replaying audio:', error);
                    handlePlayError(error, beatId);
                });
            } else {
                isPlaying = false;
                updatePlayButton(beatId, false);
                updatePlayerPlayButton(false);
                hideAudioPlayer();
                stopEqualizer(beatId);
            }
        });

        // Set up timeupdate listener
        currentAudio.addEventListener('timeupdate', updateProgress);
        currentAudio.addEventListener('loadedmetadata', updateDuration);
        currentAudio.addEventListener('error', (e) => {
            console.error('Audio error:', e);
            handleAudioError(e, beatId);
        });

        // Play the audio
        currentAudio.play().catch(error => {
            console.error('Error playing audio:', error);
            handlePlayError(error, beatId);
        });
    } catch (error) {
        console.error('Error in playSample:', error);
        handlePlayError(error, beatId);
    }
}

// Handle play errors
function handlePlayError(error, beatId) {
    isPlaying = false;
    updatePlayButton(beatId, false);
    updatePlayerPlayButton(false);
    stopEqualizer(beatId);
    
    // Show error message to user
    const player = document.getElementById('audioPlayer');
    if (player) {
        const errorMessage = player.querySelector('.error-message');
        if (errorMessage) {
            errorMessage.textContent = 'Error playing audio. Please try again.';
            errorMessage.classList.remove('hidden');
            setTimeout(() => {
                errorMessage.classList.add('hidden');
            }, 3000);
        }
    }
}

// Handle audio errors
function handleAudioError(error, beatId) {
    isPlaying = false;
    updatePlayButton(beatId, false);
    updatePlayerPlayButton(false);
    stopEqualizer(beatId);
    
    // Show error message to user
    const player = document.getElementById('audioPlayer');
    if (player) {
        const errorMessage = player.querySelector('.error-message');
        if (errorMessage) {
            errorMessage.textContent = 'Error loading audio. Please try again.';
            errorMessage.classList.remove('hidden');
            setTimeout(() => {
                errorMessage.classList.add('hidden');
            }, 3000);
        }
    }
}

// Update progress bar and time display
function updateProgress() {
    if (!currentAudio || isSeeking) return;
    
    const player = document.getElementById('audioPlayer');
    if (!player) return;

    const progressBar = player.querySelector('.audio-progress');
    const currentTime = player.querySelector('.current-time');
    
    if (progressBar && currentTime) {
        const progress = (currentAudio.currentTime / currentAudio.duration) * 100;
        progressBar.value = progress;
        currentTime.textContent = formatTime(currentAudio.currentTime);
    }
}

// Update duration display
function updateDuration() {
    if (!currentAudio) return;
    
    const player = document.getElementById('audioPlayer');
    if (!player) return;

    const duration = player.querySelector('.duration');
    if (duration) {
        duration.textContent = formatTime(currentAudio.duration);
    }
}

// Update play button state in the beat card
function updatePlayButton(beatId, isPlaying) {
    // Update all instances of the beat card with the same ID
    const buttons = document.querySelectorAll(`[data-beat-id="${beatId}"] .play-button i`);
    buttons.forEach(button => {
        if (button) {
            button.className = isPlaying ? 'ri-pause-fill text-white ri-lg' : 'ri-play-fill text-white ri-lg';
        }
    });
}

// Update play button state in the player
function updatePlayerPlayButton(isPlaying) {
    const player = document.getElementById('audioPlayer');
    if (!player) return;

    const playPauseBtn = player.querySelector('.play-pause-btn');
    if (playPauseBtn) {
        playPauseBtn.innerHTML = isPlaying ? 
            '<i class="ri-pause-fill ri-lg"></i>' : 
            '<i class="ri-play-fill ri-lg"></i>';
    }
}

// Show audio player
function showAudioPlayer(beatId) {
    const player = document.getElementById('audioPlayer');
    // Get the first instance of the beat card
    const beat = document.querySelector(`[data-beat-id="${beatId}"]`);
    if (player && beat) {
        const title = beat.querySelector('h3').textContent;
        const genre = beat.querySelector('.bg-primary\\/80').textContent;
        const bpm = beat.querySelector('.bg-gray-800\\/80').textContent;
        const image = beat.querySelector('img').src;
        
        player.querySelector('.beat-title').textContent = title;
        player.querySelector('.beat-info').textContent = `${genre} • ${bpm}`;
        player.querySelector('img').src = image;
        player.classList.remove('hidden');
    }
}

// Hide audio player
function hideAudioPlayer() {
    const player = document.getElementById('audioPlayer');
    if (player) {
        player.classList.add('hidden');
    }
}

// Start equalizer animation
function startEqualizer(beatId) {
    // Start equalizer for all instances of the beat
    const equalizers = document.querySelectorAll(`[data-beat-id="${beatId}"] .equalizer`);
    equalizers.forEach(equalizer => {
        if (equalizer) {
            equalizer.classList.add('playing');
        }
    });
}

// Stop equalizer animation
function stopEqualizer(beatId) {
    // Stop equalizer for all instances of the beat
    const equalizers = document.querySelectorAll(`[data-beat-id="${beatId}"] .equalizer`);
    equalizers.forEach(equalizer => {
        if (equalizer) {
            equalizer.classList.remove('playing');
        }
    });
}

// Update playlist and current index
function updatePlaylist(beatId) {
    try {
        // Get all beat cards on the page
        const beatCards = document.querySelectorAll('[data-beat-id]');
        currentPlaylist = Array.from(beatCards).map(card => {
            const playButton = card.querySelector('.play-button');
            if (!playButton) return null;
            
            // Get the sample URL from the data attribute
            const sampleUrl = playButton.getAttribute('data-sample-url');
            if (!sampleUrl) return null;
            
            return {
                id: card.dataset.beatId,
                sampleUrl: sampleUrl
            };
        }).filter(beat => beat !== null);
        
        // Find current index
        currentIndex = currentPlaylist.findIndex(beat => beat.id === beatId);
        updateNavigationButtons();
    } catch (error) {
        console.error('Error updating playlist:', error);
        // Reset playlist if there's an error
        currentPlaylist = [];
        currentIndex = -1;
        updateNavigationButtons();
    }
}

// Play previous track
function playPrevious() {
    if (currentIndex > 0) {
        const prevBeat = currentPlaylist[currentIndex - 1];
        playSample(prevBeat.id, prevBeat.sampleUrl);
    }
}

// Play next track
function playNext() {
    if (currentIndex < currentPlaylist.length - 1) {
        const nextBeat = currentPlaylist[currentIndex + 1];
        playSample(nextBeat.id, nextBeat.sampleUrl);
    }
}

// Update navigation buttons state
function updateNavigationButtons() {
    const player = document.getElementById('audioPlayer');
    if (!player) return;

    const prevBtn = player.querySelector('.ri-skip-back-line').parentElement;
    const nextBtn = player.querySelector('.ri-skip-forward-line').parentElement;

    if (prevBtn) {
        prevBtn.classList.toggle('opacity-50', currentIndex <= 0);
        prevBtn.classList.toggle('cursor-not-allowed', currentIndex <= 0);
    }

    if (nextBtn) {
        nextBtn.classList.toggle('opacity-50', currentIndex >= currentPlaylist.length - 1);
        nextBtn.classList.toggle('cursor-not-allowed', currentIndex >= currentPlaylist.length - 1);
    }
}

// Initialize audio player controls
document.addEventListener('DOMContentLoaded', function() {
    const player = document.getElementById('audioPlayer');
    if (player) {
        const playPauseBtn = player.querySelector('.play-pause-btn');
        const progressBar = player.querySelector('.audio-progress');
        const volumeControl = player.querySelector('input[type="range"].w-20');
        const repeatBtn = player.querySelector('.ri-repeat-line').parentElement;
        const prevBtn = player.querySelector('.ri-skip-back-line').parentElement;
        const nextBtn = player.querySelector('.ri-skip-forward-line').parentElement;

        // Play/Pause button
        playPauseBtn.addEventListener('click', () => {
            try {
                if (currentAudio) {
                    if (isPlaying) {
                        currentAudio.pause();
                        isPlaying = false;
                        updatePlayButton(currentBeatId, false);
                        updatePlayerPlayButton(false);
                    } else {
                        currentAudio.play().catch(error => {
                            console.error('Error playing audio:', error);
                            handlePlayError(error, currentBeatId);
                        });
                        isPlaying = true;
                        updatePlayButton(currentBeatId, true);
                        updatePlayerPlayButton(true);
                    }
                }
            } catch (error) {
                console.error('Error in play/pause:', error);
                handlePlayError(error, currentBeatId);
            }
        });

        // Progress bar
        progressBar.addEventListener('mousedown', () => {
            isSeeking = true;
            // Pause the audio while seeking to prevent buffering issues
            if (currentAudio && isPlaying) {
                currentAudio.pause();
            }
        });

        progressBar.addEventListener('input', (e) => {
            try {
                if (currentAudio) {
                    const time = (e.target.value / 100) * currentAudio.duration;
                    const currentTime = player.querySelector('.current-time');
                    if (currentTime) {
                        currentTime.textContent = formatTime(time);
                    }
                }
            } catch (error) {
                console.error('Error updating seek position:', error);
            }
        });

        progressBar.addEventListener('mouseup', () => {
            try {
                if (currentAudio) {
                    const time = (progressBar.value / 100) * currentAudio.duration;
                    // Set the time and wait for it to be ready
                    currentAudio.currentTime = time;
                    
                    // Add a small delay before playing to ensure the audio is ready
                    setTimeout(() => {
                        if (isPlaying) {
                            currentAudio.play().catch(error => {
                                console.error('Error playing audio after seek:', error);
                                handlePlayError(error, currentBeatId);
                            });
                        }
                    }, 100);
                }
            } catch (error) {
                console.error('Error in seek operation:', error);
                handlePlayError(error, currentBeatId);
            }
            isSeeking = false;
        });

        // Volume control
        volumeControl.addEventListener('input', (e) => {
            try {
                volume = e.target.value / 100;
                if (currentAudio) {
                    currentAudio.volume = volume;
                }
            } catch (error) {
                console.error('Error setting volume:', error);
            }
        });

        // Repeat button
        repeatBtn.addEventListener('click', () => {
            isRepeat = !isRepeat;
            repeatBtn.classList.toggle('text-primary', isRepeat);
        });

        // Previous button
        prevBtn.addEventListener('click', () => {
            if (currentIndex > 0) {
                playPrevious();
            }
        });

        // Next button
        nextBtn.addEventListener('click', () => {
            if (currentIndex < currentPlaylist.length - 1) {
                playNext();
            }
        });
    }
});

// Format time in MM:SS
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}