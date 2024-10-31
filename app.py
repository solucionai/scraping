from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
import random

app = Flask(__name__)

# Configuração do ChromeDriver com WebDriver Manager e opções anti-detecção
def configure_driver():
    options = webdriver.ChromeOptions()
    # Remover a linha com binary_location para evitar problemas no servidor
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--headless")  # Adiciona modo headless para produção
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Função para realizar o scraping e retornar o conteúdo das jurisprudências como lista de dicionários
def scrape_tjsp(term):
    driver = configure_driver()
    url = "https://esaj.tjsp.jus.br/cjsg/consultaCompleta.do?f=1"
    driver.get(url)
    sleep(2)

    # Inserir termo de busca no campo "Pesquisa Livre"
    search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "iddados.buscaInteiroTeor")))
    search_box.send_keys(term)

    # Submeter a pesquisa clicando no botão "Pesquisar"
    search_button = driver.find_element(By.ID, "pbSubmit")
    search_button.click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "tdResultados")))

    results_content = []  # Lista para armazenar os resumos de jurisprudência como dicionários

    # Loop para processar cada resultado
    results = driver.find_elements(By.CSS_SELECTOR, "tr.fundocinza1, tr.fundocinza2")
    for index in range(len(results)):
        try:
            results = driver.find_elements(By.CSS_SELECTOR, "tr.fundocinza1, tr.fundocinza2")
            result = results[index]
            
            numero_processo_element = result.find_element(By.XPATH, ".//a[contains(@class, 'esajLinkLogin')]")
            numero_processo = numero_processo_element.text
            cd_acordao = numero_processo_element.get_attribute("cdacordao")
            pdf_url = f"https://esaj.tjsp.jus.br/cjsg/getArquivo.do?cdAcordao={cd_acordao}&cdForo=0"
            
            classe_assunto = result.find_element(By.XPATH, ".//strong[contains(text(), 'Classe/Assunto:')]/parent::td").text
            relator = result.find_element(By.XPATH, ".//strong[contains(text(), 'Relator(a):')]/parent::td").text
            comarca = result.find_element(By.XPATH, ".//strong[contains(text(), 'Comarca:')]/parent::td").text
            orgao_julgador = result.find_element(By.XPATH, ".//strong[contains(text(), 'Órgão julgador:')]/parent::td").text
            data_julgamento = result.find_element(By.XPATH, ".//strong[contains(text(), 'Data do julgamento:')]/parent::td").text
            data_publicacao = result.find_element(By.XPATH, ".//strong[contains(text(), 'Data de publicação:')]/parent::td").text

            try:
                expand_button = result.find_element(By.XPATH, ".//img[contains(@class, 'mostrarOcultarEmenta')]")
                expand_button.click()
                sleep(1)
                ementa = result.find_element(By.XPATH, ".//div[2]").text
            except:
                ementa_element = result.find_elements(By.XPATH, ".//div[contains(@id, 'ementa')]")
                ementa = ementa_element[0].text if ementa_element else "Ementa não disponível"
            
            jurisprudencia_content = {
                "processo": numero_processo,
                "classe_assunto": classe_assunto,
                "relator": relator,
                "comarca": comarca,
                "orgao_julgador": orgao_julgador,
                "data_julgamento": data_julgamento,
                "data_publicacao": data_publicacao,
                "ementa": ementa,
                "pdf_url": pdf_url
            }
            results_content.append(jurisprudencia_content)
            print(f"Salvo resumo para Jurisprudência - {index + 1} - Processo: {numero_processo}")
            
            sleep(random.uniform(1, 2))

        except Exception as e:
            print(f"Erro ao processar resultado {index + 1}: {e}")
            continue

    driver.quit()
    return results_content

# Endpoint da API para buscar jurisprudência
@app.route('/search', methods=['POST'])
def search():
    data = request.json
    term = data.get('term')
    results = scrape_tjsp(term)
    return jsonify(results)

# Rota GET para verificar o status da API
@app.route('/')
def home():
    return "API está funcionando. Acesse /search via POST para realizar a busca."

if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=8080)
