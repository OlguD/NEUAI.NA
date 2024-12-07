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
let studentImageHtml = null; // Öğrenci fotoğrafını saklamak için yeni değişken

// Durum değişkenleri
let isVideoRunning = false;
let isObjectDetected = false;
let currentObjectType = null;
let detectionInterval = null;

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    startButton.addEventListener('click', startVideo);
    stopButton.addEventListener('click', stopVideo);
    faceAnalyzeButton.addEventListener('click', analyzeFace);
    documentAnalyzeButton.addEventListener('click', analyzeDocument);
    resetButton.addEventListener('click', resetAnalysis);
    
    schoolNumberInput.addEventListener('keypress', async function(e) {
        if(e.key === 'Enter') {
            e.preventDefault();
            const inputValue = schoolNumberInput.value.trim();
            if (inputValue) {
                schoolNumber = inputValue;
                await searchStudentByNumber(inputValue);
            }
        }
    });

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
    schoolNumber = null;
    documentAnalysisResults = null;
    studentImageHtml = null;
    similarityResults.innerHTML = '<div class="result-item"><p>No analysis has been done yet</p></div>';
    
    if (schoolNumberInput) {
        schoolNumberInput.value = '';
    }

    faceAnalyzeButton.classList.remove('active');
    documentAnalyzeButton.classList.remove('active');
    
    resetButton.disabled = true;
    
    showMessage('Analysis results have been reset. You can start a new analysis.');
    
    setTimeout(() => {
        if (isVideoRunning) {
            detectObject();
        }
    }, 1500);
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
    
    if (!schoolNumber) {
        similarityResults.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                Please enter a school number first
            </div>
        `;
        return;
    }

    // Loading göster
    similarityResults.innerHTML = `
        <div class="loading-container">
            <div class="loader"></div>
            <span>Face analysis in progress...</span>
        </div>
    `;
    
    try {
        const response = await fetch('/analyze_face', {
            headers: {
                'X-School-Number': schoolNumber
            }
        });
        const data = await response.json();
        
        let resultHtml = '';
        
        // Sadece öğrencinin okul numarasını göster
        if (!documentAnalysisResults) {
            resultHtml += `
                <div class="document-analysis-results">
                    <div class="result-item">
                        <h3>Student Information</h3>
                        <p>Student Number: <span class="score">${schoolNumber}</span></p>
                    </div>
                </div>
            `;
        }

        // Öğrenci fotoğrafını göster
        resultHtml += `
            <div class="result-item">
                <div class="student-image">
                    <img src="/get_student_image/${schoolNumber}" alt="Student Image" 
                         style="width: 100px; height: 120px; object-fit: cover;">
                </div>
            </div>
        `;
        
        // Yüz analizi sonuçlarını ekle
        if (data.error) {
            resultHtml += `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    ${data.error}
                </div>
            `;
        } else {
            // resultHtml += `
            //     <div class="result-item">
            //         <h3>Face Analysis Results</h3>
            //         <p>Similarity Score: <span class="score">${data.similarity_score.toFixed(1)}%</span></p>
            //         <p>Cosine Similarty: <span class="score">${data.cosine_similarity.toFixed(3)}</span></p>
            //         <p>Euclidean Distance: <span class="score">${data.euclidean_distance.toFixed(3)}</span></p>
            //         <p>Result: <span class="score">${data.interpretation}</span></p>
            //     </div>
            // `;
            resultHtml += `
                <div class="result-item">
                    <h3>Face Analysis Results</h3>
                    <p>Similarity Score: <span class="score">${data.similarity_score.toFixed(1)}%</span></p>
                    <p>Result: <span class="score">${data.interpretation}</span></p>
                </div>
            `;
        }
        
        // Belge analizi sonuçları varsa ekle
        if (documentAnalysisResults) {
            resultHtml += `
                <div class="result-item">
                    <h3>Document Information</h3>
                    ${documentAnalysisResults.name_surname ? `<p>Name Surname: <span class="score">${documentAnalysisResults.name_surname}</span></p>` : ''}
                    ${documentAnalysisResults.department ? `<p>Department: <span class="score">${documentAnalysisResults.department}</span></p>` : ''}
                    ${documentAnalysisResults.class ? `<p>Class: <span class="score">${documentAnalysisResults.class}</span></p>` : ''}
                </div>
            `;
        }

        similarityResults.innerHTML = resultHtml;
        resetButton.style.display = 'inline-flex';
        
    } catch (error) {
        similarityResults.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                An error occurred while making analysis: ${error.message}
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
        
        documentAnalysisResults = data;
        schoolNumber = data.student_no;
        
        let resultHtml = `
            <div class="document-analysis-results">
                <div class="result-item">
                    <h3>Document Information</h3>
                    ${data.name_surname ? `<p>Name Surname: <span class="score">${data.name_surname}</span></p>` : ''}
                    ${data.department ? `<p>Department: <span class="score">${data.department}</span></p>` : ''}
                    ${data.class ? `<p>Class: <span class="score">${data.class}</span></p>` : ''}
                </div>
            </div>
        `;

        similarityResults.innerHTML = resultHtml;
        resetButton.style.display = 'inline-flex';

        // Öğrenci fotoğrafını bul ve göster
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

async function searchStudentByNumber(studentNumber) {
    if (!studentNumber) return;

    // Loading göster
    similarityResults.innerHTML = `
        <div class="loading-container">
            <div class="loader"></div>
            <span>Searching for student...</span>
        </div>
    `;

    try {
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

        let resultHtml = `
            <div class="document-analysis-results">
                <div class="result-item">
                    <h3>Student Information</h3>
                    <p>Student Number: <span class="score">${studentNumber}</span></p>
                </div>
                <div class="result-item">
                    <div class="student-image">
                        <img src="/get_student_image/${studentNumber}" alt="Student Image" 
                             style="width: 100px; height: 120px; object-fit: cover;">
                    </div>
                </div>
            </div>
        `;

        similarityResults.innerHTML = resultHtml;
        resetButton.disabled = false;
        resetButton.style.display = 'inline-flex';

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