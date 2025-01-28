from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime
import json
import logging
import os
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    logging.info("Setting up the driver...")

    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument("headless")  # Opsional, untuk menjalankan Chrome di mode headless
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")  # Opsional, untuk stabilitas di beberapa sistem
    
     # Tentukan versi browser jika otomatisasi gagal
    # chromedriver_path = "/home/ubuntu/biu-task(fix)/biu-task/driver/chromedriver"  # Update this path to the location of your chromedriver.exe

    # Tentukan versi browser jika otomatisasi gagal
    chromedriver_path = "D:/Zetta-Folder/newTool/TugasBiu/biu-task/driver/chromedriver.exe"  # Update this path to the location of your chromedriver.exe
    driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)
    
    driver.implicitly_wait(10)
    logging.info("Driver setup complete.")
    
    return driver


def login(driver, username, password):
    logging.info("Logging in...")

    driver.get("https://ecampus.binainsani.ac.id/binainsani/login")
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "j_username")))
    driver.find_element(By.NAME, "j_username").send_keys(username)
    driver.find_element(By.NAME, "j_password").send_keys(password)
    remember_checkbox = driver.find_element(By.ID, "rememberMe")
    if not remember_checkbox.is_selected():
        remember_checkbox.click()
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
    logging.info("Login successful.")


def navigate_to_elearning(driver):
    logging.info("Navigating to e-Learning...")
    
    elearning_xpath = "//div[@class='z-toolbarbutton-cnt' and contains(text(), 'e-Learning')]"
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, elearning_xpath)))
    elearning_button = driver.find_element(By.XPATH, elearning_xpath)
    driver.execute_script("arguments[0].scrollIntoView(true);", elearning_button)
    driver.execute_script("arguments[0].click();", elearning_button)
    logging.info("Navigation to e-Learning complete.")

def fetch_tasks(driver):
    logging.info("Fetching tasks...")

    WebDriverWait(driver, 15).until_not(EC.presence_of_element_located((By.CLASS_NAME, "z-loading")))
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "z-label")))
    task_elements = driver.find_elements(By.XPATH, "//td[@align='left']/a[@href='javascript:;']/span[@class='z-label' and contains(text(), 'Tugas')]")
    
    tasks = []
    for index, task_element in enumerate(task_elements):
        task = {}
        parent_td = task_element.find_element(By.XPATH, "../..")
        actions = ActionChains(driver)
        actions.move_to_element(parent_td).click().perform()
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//legend[contains(@class, 'z-caption')]")))
        time.sleep(5)
        
        task['title'] = task_element.text
        
        # Tambahkan kelas dinamis ke elemen "Tugas Mulai" dan "Tugas Selesai"
        class_suffix = f"-{index}"
        driver.execute_script(f"""
            var tugasMulai = document.evaluate("//span[contains(text(), 'Tugas Mulai')]/ancestor::td/following-sibling::td//font[contains(@style, 'color:red')]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (tugasMulai) {{
                tugasMulai.className = 'tugas-mulai{class_suffix}';
            }}
            
            var tugasSelesai = document.evaluate("//span[contains(text(), 'Tugas Selesai')]/ancestor::td/following-sibling::td//font[contains(@style, 'color:red')]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (tugasSelesai) {{
                tugasSelesai.className = 'tugas-selesai{class_suffix}';
            }}
        """)
        
        try:
            end_element = driver.find_element(By.CSS_SELECTOR, f".tugas-selesai{class_suffix}")
            task['end'] = end_element.text if end_element else "N/A"
        except Exception as e:
            task['end'] = "N/A"

        try:
            start_element = driver.find_element(By.CSS_SELECTOR, f".tugas-mulai{class_suffix}")
            task['start'] = start_element.text if start_element else "N/A"
        except Exception as e:
            task['start'] = "N/A"
        
        # Hapus kelas dinamis setelah mengambil data
        driver.execute_script(f"""
            var tugasMulai = document.querySelector('.tugas-mulai{class_suffix}');
            if (tugasMulai) {{
                tugasMulai.classList.remove('tugas-mulai{class_suffix}');
            }}
            
            var tugasSelesai = document.querySelector('.tugas-selesai{class_suffix}');
            if (tugasSelesai) {{
                tugasSelesai.classList.remove('tugas-selesai{class_suffix}');
            }}
        """)
        
        tasks.append(task)
        
        # Cari tombol "Selesai" yang terbaru dan hitung jumlahnya
        close_button_xpath = "//div[@title='Tutup ' and contains(@class, 'z-toolbarbutton')]"
        try:
            close_buttons = parent_td.find_elements(By.XPATH, close_button_xpath)
            if close_buttons:
                close_button = close_buttons[-1]  # Ambil tombol terakhir yang baru
                if close_button.is_displayed() and close_button.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView(true);", close_button)
                    driver.execute_script("arguments[0].click();", close_button)
        except Exception as e:
            pass
        
        time.sleep(3)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "z-label")))
    logging.info("Tasks fetched successfully.")

    return tasks

def check_deadlines(tasks):
    logging.info("Checking deadlines...")

    for task in tasks:
        if "lalu" in task['end'].lower():
            task['status'] = "Overdue"
        else:
            try:
                if task['end'].strip() and task['end'] != "N/A":
                    task_end_datetime = datetime.strptime(task['end'].split(", ")[-1], '%d-%m-%Y %H:%M:%S')
                    days_left = (task_end_datetime - datetime.now()).days
                    if days_left < 0:
                        task['status'] = "Overdue"
                    elif days_left == 0:
                        task['status'] = "Due Today"
                    elif days_left == 1:
                        task['status'] = "Due Tomorrow"
                    else:
                        task['status'] = f"Due in {days_left} days"
                else:
                    task['status'] = "No End Date"
            except ValueError:
                task['status'] = "Invalid Date"
        logging.info("Deadlines checked successfully.")

    return tasks


def cek_status_tugas(driver, username):
    logging.info("Checking task status...")

    # Memeriksa apakah terdapat elemen yang menunjukkan tugas belum dikumpulkan
    belum_kumpul_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'Anda belum mengumpulkan / meng-upload')]")
    logging.info(f"Found {len(belum_kumpul_elements)} 'belum dikumpulkan' elements.")
    
    # Memeriksa apakah terdapat elemen yang menunjukkan tugas telah dikumpulkan
    sudah_kumpul_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'z-toolbarbutton') and contains(@title, 'Lihat / Download')]")
    logging.info(f"Found {len(sudah_kumpul_elements)} 'sudah dikumpulkan' elements.")

    response = driver.execute_script("""
        var userButtonProfile = document.querySelector('a.user_button_profile');
        var userProfile = userButtonProfile ? userButtonProfile.querySelector('span.z-label').innerText : 'Tidak Ditemukan';

        var legendaRows = document.evaluate("//legend[contains(@class, 'z-caption')]", document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
        var legendaArray = [];
        for (var i = 0; i < legendaRows.snapshotLength; i++) {
            legendaArray.push(legendaRows.snapshotItem(i));
        }

        var tugasRows = document.evaluate("//tr[contains(@class, 'fgrid z-row') and (.//span[contains(text(), 'Tugas Mulai')] or .//span[contains(text(), 'Tugas Selesai')])]", document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);

        function getMataKuliahForTugas(tugasRow) {
            for (var i = legendaArray.length - 1; i >= 0; i--) {
                if (legendaArray[i].compareDocumentPosition(tugasRow) & Node.DOCUMENT_POSITION_FOLLOWING) {
                    return document.evaluate(".//span[contains(@id, '-cnt')]", legendaArray[i], null, XPathResult.STRING_TYPE, null).stringValue;
                }
            }
            return "Tidak Ditemukan";
        }

        var printedTugas = new Set();
        var results = [];
        var alerts = [];

        for (var i = 0; i < tugasRows.snapshotLength; i++) {
            var tugasRow = tugasRows.snapshotItem(i);
            var tugasMulaiText = "";
            var tugasSelesaiText = "";
            var mataKuliahText = getMataKuliahForTugas(tugasRow);

            // Cari teks dari elemen "Tugas Mulai"
            if (document.evaluate(".//span[contains(text(), 'Tugas Mulai')]", tugasRow, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue) {
                tugasMulaiText = document.evaluate(".//span[contains(text(), 'Tugas Mulai')]/ancestor::td/following-sibling::td//font[contains(@style, 'color:red')]", tugasRow, null, XPathResult.STRING_TYPE, null).stringValue;
            }

            // Cari teks dari elemen "Tugas Selesai"
            if (document.evaluate(".//span[contains(text(), 'Tugas Selesai')]", tugasRow, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue) {
                tugasSelesaiText = document.evaluate(".//span[contains(text(), 'Tugas Selesai')]/ancestor::td/following-sibling::td//font[contains(@style, 'color:red')]", tugasRow, null, XPathResult.STRING_TYPE, null).stringValue;
            }

            // Gabungkan tugas dalam satu objek
            var tugasObject = results.find(function(tugas) { 
                return tugas.MataKuliah === mataKuliahText;
            });
            if (!tugasObject) {
                tugasObject = { "MataKuliah": mataKuliahText, "Tugas Mulai": tugasMulaiText, "Tugas Selesai": tugasSelesaiText };
                results.push(tugasObject);
            } else {
                if (!tugasObject["Tugas Mulai"] && tugasMulaiText) tugasObject["Tugas Mulai"] = tugasMulaiText;
                if (!tugasObject["Tugas Selesai"] && tugasSelesaiText) tugasObject["Tugas Selesai"] = tugasSelesaiText;
            }

            // Perhitungan sisa hari
            var dateMatch = tugasSelesaiText.match(/\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}/);
            if (dateMatch) {
                var tugasSelesaiDateStr = dateMatch[0].replace(/(\d{2})-(\d{2})-(\d{4})/, '$3/$2/$1'); // Ubah format dd-mm-yyyy menjadi yyyy/mm/dd
                var tugasSelesaiDate = new Date(tugasSelesaiDateStr);
                var sekarang = new Date();
                var sisaHari = (tugasSelesaiDate - sekarang) / (1000 * 60 * 60 * 24);
                if (sisaHari >= 0 && sisaHari < 4) {
                    alerts.push(`Tugas ${mataKuliahText} sisa ${Math.ceil(sisaHari)} hari.`);
                } else if (sisaHari < 0) {
                    alerts.push(`Tugas ${mataKuliahText} terlewat ${Math.abs(Math.ceil(sisaHari))} hari yang lalu.`);
                }
            } else {
                alerts.push(`Format tanggal tidak valid: ${tugasSelesaiText}`);
            }
        }

        function cekStatusTugas() {
            var statusResults = [];
            var fieldsetBelumKumpul = document.evaluate("//span[contains(text(), 'Anda belum mengumpulkan / meng-upload')]", document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
            var fieldsetSudahKumpul = document.evaluate("//div[contains(@class, 'z-toolbarbutton') and contains(@title, 'Lihat / Download')]", document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);

            if (fieldsetBelumKumpul.snapshotLength > 0) {
                for (var i = 0; i < fieldsetBelumKumpul.snapshotLength; i++) {
                    var elemenBelum = fieldsetBelumKumpul.snapshotItem(i);
                    var parentFieldset = elemenBelum.closest('fieldset');
                    var userInfoElement = parentFieldset ? parentFieldset.querySelector('.z-label') : null;
                    if (userInfoElement) {
                        var userInfo = userInfoElement.innerText;
                        statusResults.push({ "Status Tugas": "Belum Dikumpulkan", "Detail Belum Kumpul": elemenBelum.innerText, "User Info": userInfo });
                    }
                }
            }

            if (fieldsetSudahKumpul.snapshotLength > 0) {
                for (var j = 0; j < fieldsetSudahKumpul.snapshotLength; j++) {
                    var elemenSudah = fieldsetSudahKumpul.snapshotItem(j);
                    var parentFieldset = elemenSudah.closest('fieldset');
                    var userInfoElement = parentFieldset ? parentFieldset.querySelector('.z-label') : null;
                    if (userInfoElement) {
                        var userInfo = userInfoElement.innerText;
                        statusResults.push({ "Status Tugas": "Sudah Dikumpulkan", "Detail Tugas": elemenSudah.title, "User Info": userInfo });
                    }
                }
            }

            return statusResults;
        }

        var statusResults = cekStatusTugas();
        return { "userProfile": userProfile, "results": results, "statusResults": statusResults, "alerts": alerts };
    """)

    # Now you can access the combined object
    userProfile = response['userProfile']
    results = response['results']
    statusResults = response['statusResults']
    alerts = response['alerts']

    # Generate JSON content for the current user
    user_json_content = {
        "username": username,
        "userProfile": userProfile,
        "results": results,
        "statusResults": statusResults,
        "alerts": alerts
    }
    print(user_json_content)
    # Load existing JSON data if it exists
    json_file_path = "hasil_tugas.json"
    if os.path.exists(json_file_path):
        with open(json_file_path, "r", encoding="utf-8") as file:
            all_users_data = json.load(file)
    else:
        all_users_data = []

    # Ensure all_users_data is a list of dictionaries
    if not isinstance(all_users_data, list):
        all_users_data = []

    # Check if the user already exists in the JSON data
    user_exists = False
    for user_data in all_users_data:
        if isinstance(user_data, dict) and user_data.get("username") == user_json_content["username"]:
            user_data.update(user_json_content)
            user_exists = True
            break

    # If the user does not exist, append the new user data
    if not user_exists:
        all_users_data.append(user_json_content)

    # Save the updated JSON data
    with open(json_file_path, "w", encoding="utf-8") as file:
        json.dump(all_users_data, file, ensure_ascii=False, indent=4)
    logging.info("JSON TERSIMPAN")

def fetch_elearning_tasks(username, password):
    logging.info("Starting fetch_elearning_tasks...")

    driver = setup_driver()
    try:
        login(driver, username, password)
        navigate_to_elearning(driver)
        tasks = fetch_tasks(driver)
        tasks = check_deadlines(tasks)
        cek_status_tugas(driver, username)
        logging.info(f"Tasks: {tasks}")
        return tasks
    finally:
        logging.info("Quitting driver...")

        print("quit")
        driver.quit()
        logging.info("Driver quit successfully.")
        print("sukses quit")

# ...existing code...