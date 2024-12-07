// DOM elementlerini global olarak tanımla
const videoFeed = document.getElementById('videoFeed');
const placeholderImage = document.getElementById('placeholderImage');
const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');
const faceAnalyzeButton = document.getElementById('faceAnalyzeButton');
const documentAnalyzeButton = document.getElementById('documentAnalyzeButton');
const detectionMessage = document.getElementById('detectionMessage');
const similarityResults = document.getElementById('similarityResults');
const loadingAnimation = document.getElementById('loadingAnimation');
const resetButton = document.getElementById('resetButton');
const controlsSecondary = document.querySelector('.controls-secondary');
const searchIcon = document.getElementsByClassName('search-icon')[0];
const schoolNumberInput = document.getElementById('schoolNumber');

let schoolNumber;
let documentAnalysisResults = null;

// Durum değişkenleri
let isVideoRunning = false;
let isObjectDetected = false;
let currentObjectType = null;
let detectionInterval = null;

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // hideLoadingAnimation();
    startButton.addEventListener('click', startVideo);
    stopButton.addEventListener('click', stopVideo);
    faceAnalyzeButton.addEventListener('click', analyzeFace);
    documentAnalyzeButton.addEventListener('click', analyzeDocument);
    resetButton.addEventListener('click', resetAnalysis);
    
    schoolNumberInput.addEventListener('keypress', async function(e) {
        if (e.key === 'Enter') {
            e.preventDefault(); // Form submission'ı engelle
            const inputValue = schoolNumberInput.value.trim();
            
            if (inputValue) {
                schoolNumber = inputValue;
                await findStudentByNumber(schoolNumber);
            }
        }
    });

    // Change this line to show the button but keep it disabled
    resetButton.disabled = true;
});

function showLoadingAnimation() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.style.display = 'flex';
    }
}

function hideLoadingAnimation() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.style.display = 'none';
    }
}

function resetAnalysis() {
    // Reset analysis results
    schoolNumber = null;
    documentAnalysisResults = null;
    similarityResults.innerHTML = '<div class="result-item"><p>No analysis has been done yet</p></div>';
    
    if (schoolNumberInput) {
        schoolNumberInput.value = '';
    }

    // Reset buttons but don't disable them
    faceAnalyzeButton.classList.remove('active');
    documentAnalyzeButton.classList.remove('active');
    
    // Reset button should be disabled until next detection
    resetButton.disabled = true;
    
    // Show message
    showMessage('Analysis results have been reset. You can start a new analysis.');
    
    // Add delay before restarting detection
    setTimeout(() => {
        if (isVideoRunning) {
            detectObject();
        }
    }, 1500); // 1.5 second delay
}

function startVideo() {
    console.log("Starting Stream...");
    isVideoRunning = true;
    isObjectDetected = false;
    currentObjectType = null;
    
    videoFeed.src = videoFeed.dataset.videoUrl;
    videoFeed.style.display = 'block';
    placeholderImage.style.display = 'none';
    
    startButton.style.display = 'none';
    stopButton.style.display = 'inline-flex';

    controlsSecondary.style.display = 'flex';
    
    // Butonları sıfırla
    faceAnalyzeButton.disabled = true;
    documentAnalyzeButton.disabled = true;
    resetButton.disabled = true;  // Keep reset disabled until detection
    
    // Nesne tespitini başlat
    detectObject();
}

function stopVideo() {
    console.log("Stoping Stream...");
    isVideoRunning = false;
    isObjectDetected = false;
    currentObjectType = null;
    
    videoFeed.src = "";
    videoFeed.style.display = 'none';
    placeholderImage.style.display = 'flex';
    
    startButton.style.display = 'inline-flex';
    stopButton.style.display = 'none';
    
    // Butonları devre dışı bırak
    faceAnalyzeButton.disabled = true;
    documentAnalyzeButton.disabled = true;

    controlsSecondary.style.display = 'none';
}

function detectObject() {
    if (!isVideoRunning) return;

    fetch('/detect_object')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error("Detection Error:", data.error);
                if (isVideoRunning) setTimeout(detectObject, 500);
                return;
            }

            if (data.type === 'face' || data.type === 'document') {
                resetButton.disabled = false;  // Enable reset button on first detection
                if (data.type === 'face') {
                    currentObjectType = 'face';
                    faceAnalyzeButton.disabled = false;
                    documentAnalyzeButton.disabled = true;
                    faceAnalyzeButton.classList.add('active');
                    documentAnalyzeButton.classList.remove('active');
                    showMessage('Face detected - You can analyze the face');
                }
                else if (data.type === 'document') {
                    currentObjectType = 'document';
                    documentAnalyzeButton.disabled = false;
                    faceAnalyzeButton.disabled = true;
                    documentAnalyzeButton.classList.add('active');
                    faceAnalyzeButton.classList.remove('active');
                    showMessage('Document detected - You can analyze the document');
                }
            }
            else {
                faceAnalyzeButton.classList.remove('active');
                documentAnalyzeButton.classList.remove('active');
                if (isVideoRunning) setTimeout(detectObject, 500);
            }
        })
        .catch(error => {
            console.error("Detection Error:", error);
            if (isVideoRunning) setTimeout(detectObject, 500);
        });
}

function showMessage(text) {
    if (detectionMessage) {
        detectionMessage.innerHTML = `
            <div class="success-message">
                <i class="fas fa-check-circle"></i>
                ${text}
            </div>
        `;
    }
}

async function analyzeFace() {
    if (!isVideoRunning || currentObjectType !== 'face') return;
    
    // Önceki belge analizi sonuçlarını sakla
    const previousResults = similarityResults.innerHTML;
    
    // Loading göster
    similarityResults.innerHTML = `
        <div class="loading-container">
            <div class="loader"></div>
            <span>Face analysis in progress...</span>
        </div>
    `;
    
    try {
        const response = await fetch('/analyze_face');
        const data = await response.json();
        
        let newResultsHtml = '';
        
        if (data.error) {
            newResultsHtml = `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    ${data.error}
                </div>
            `;
        } else {
            newResultsHtml = `
                <div class="result-item">
                    <h3>Face Analysis Results</h3>
                    <p>Similarity Score: <span class="score">${data.similarity_score.toFixed(1)}%</span></p>
                    <p>Cosine Similarty: <span class="score">${data.cosine_similarity.toFixed(3)}</span></p>
                    <p>Euclidean Distance: <span class="score">${data.euclidean_distance.toFixed(3)}</span></p>
                    <p>Result: <span class="score">${data.interpretation}</span></p>
                </div>
            `;
        }
        
        // Eski sonuçları küçültülmüş şekilde alt kısma ekle
        if (documentAnalysisResults) {
            similarityResults.innerHTML = newResultsHtml + `
                <div class="previous-results" style="margin-top: 20px; font-size: 0.9em; opacity: 0.8;">
                    <h4>Previous Document Analysis</h4>
                    ${previousResults}
                </div>
            `;
        } else {
            similarityResults.innerHTML = newResultsHtml;
        }

        resetButton.style.display = 'inline-flex';
        
    } catch (error) {
        similarityResults.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                An error occurred while making analysis: ${error.message}
            </div>
            <div class="previous-results" style="margin-top: 20px; font-size: 0.9em; opacity: 0.8;">
                ${previousResults}
            </div>
        `;
    }
}

async function analyzeDocument() {
    if (!isVideoRunning || currentObjectType !== 'document') return;
    
    similarityResults.innerHTML = `
        <div class="loading-container">
            <div class="loader"></div>
            <span>Document analysis in progress...</span>
        </div>
    `;
    
    try {
        const response = await fetch('/document_analysis');
        const data = await response.json();
        
        if (data.error) {
            similarityResults.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    ${data.error}
                </div>
            `;
            return;
        }
        
        // Belge analizi sonuçlarını sakla
        documentAnalysisResults = data;
        schoolNumber = data.student_no;
        
        let resultHtml = `
            <div class="document-analysis-results">
                <div class="result-item">
                    <h3>Document Information</h3>
        `;
        
        if (data.student_no) resultHtml += `<p>Student Number: <span class="score">${data.student_no}</span></p>`;
        if (data.name_surname) resultHtml += `<p>Name Surname: <span class="score">${data.name_surname}</span></p>`;
        if (data.department) resultHtml += `<p>Department: <span class="score">${data.department}</span></p>`;
        if (data.class) resultHtml += `<p>Class: <span class="score">${data.class}</span></p>`;

        resultHtml += `</div>`;
        similarityResults.innerHTML = resultHtml;

        resetButton.style.display = 'inline-flex';

        await findStudent(similarityResults);


    } catch (error) {
        similarityResults.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                An error occurred while making analysis: ${error.message}
            </div>
        `;
    }
}

async function findStudentByNumber(studentNumber) {
    try {
        // Loading göster
        similarityResults.innerHTML = `
            <div class="loading-container">
                <div class="loader"></div>
                <span>Searching for student ${studentNumber}...</span>
            </div>
        `;

        const response = await fetch('/find_student', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-School-Number': studentNumber
            }
        });

        const data = await response.json();

        if (data.error) {
            similarityResults.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    ${data.error}
                </div>
            `;
            return;
        }

        // Öğrenci bilgilerini göster
        let resultHtml = `
            <div class="result-item">
                <h3>Student Information</h3>
                <div class="student-image">
                    <img src="/get_student_image/${studentNumber}" alt="Student Image" 
                         style="width: 100px; height: 120px; object-fit: cover;">
                </div>
            </div>
        `;

        similarityResults.innerHTML = resultHtml;

        // Reset butonunu aktif et
        resetButton.disabled = false;

    } catch (error) {
        similarityResults.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                An error occurred during the search: ${error.message}
            </div>
        `;
    }
}

async function findStudent(similarityResults) {
    const currentContent = similarityResults.innerHTML;
    
    similarityResults.innerHTML += `
        <div id="loadingContainer" class="loading-container">
            <div class="loader"></div>
            <span>Searching for student...</span>
        </div>
    `;
 
    try {
        if (!schoolNumber) {
            similarityResults.innerHTML += `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Student not found</p>
                </div>
            `;
            return;
        }
 
        const response = await fetch('/find_student', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-School-Number': schoolNumber
            }
        });
 
        const data = await response.json();
        
        if (data.error) {
            similarityResults.innerHTML += `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    ${data.error}
                </div>
            `;
            return;
        }
        
        let resultHtml = `
            <div class="result-item">
                <h3>Student Information</h3>
                <div class="student-image">
                    <img src="/get_student_image/${schoolNumber}" alt="Student Image" 
                         style="width: 100px; height: 120px; object-fit: cover;">
                </div>
            </div>
        `;
        
        similarityResults.innerHTML = currentContent + resultHtml;
 
    } catch (error) {
        similarityResults.innerHTML += `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                An error occurred during the search: ${error.message}
            </div>
        `;
    } finally {
        const loadingContainer = document.getElementById('loadingContainer');
        if (loadingContainer) {
            loadingContainer.remove();
        }
    }
}