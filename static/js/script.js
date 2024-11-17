let streamStarted = false;

function toggleStream() {
    const videoFeed = document.getElementById('video-feed');
    const button = document.querySelector('.btn-success');
    if (streamStarted) {
        videoFeed.style.display = 'none';
        videoFeed.src = '';
        button.textContent = 'Start Stream';
    } else {
        videoFeed.style.display = 'block';
        fetch('/video_feed')
            .then(response => {
                if (response.ok) {
                    videoFeed.src = response.url;
                } else {
                    console.error('Error fetching video feed:', response.statusText);
                }
            })
            .catch(error => console.error('Error:', error));
        button.textContent = 'Stop Stream';
    }
    streamStarted = !streamStarted;
}

function analyzeImage() {
    if (!streamStarted) {
        alert('Please start the video stream first.');
        return;
    }
    fetch('/analyze_image')
        .then(response => response.json())
        .then(data => {
            document.getElementById('analysis-result').innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        })
        .catch(error => console.error('Error:', error));
}

function documentAnalysis() {
    if (!streamStarted) {
        alert('Please start the video stream first.');
        return;
    }
    fetch('/document_analysis')
        .then(response => response.json())
        .then(data => {
            document.getElementById('analysis-result').innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        })
        .catch(error => console.error('Error:', error));
}