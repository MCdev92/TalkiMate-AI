const startRecordingButton = document.getElementById('startRecording');
const stopRecordingButton = document.getElementById('stopRecording');
const responseSection = document.getElementById('responseSection');
const responseText = document.getElementById('responseText');
const audioPlayer = document.getElementById('audioPlayer');
const audioSource = document.getElementById('audioSource');

let mediaRecorder;
let audioChunks = [];

startRecordingButton.addEventListener('click', async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        audioChunks = [];

        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');

        const response = await fetch('/process_audio', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();
        responseText.textContent = data.response_text;
        audioSource.src = data.audio_url;
        audioPlayer.style.display = 'block';
        audioPlayer.load();
        responseSection.style.display = 'block';
    };

    mediaRecorder.start();
    startRecordingButton.style.display = 'none';
    stopRecordingButton.style.display = 'inline';
});

stopRecordingButton.addEventListener('click', () => {
    mediaRecorder.stop();
    stopRecordingButton.style.display = 'none';
    startRecordingButton.style.display = 'inline';
});
