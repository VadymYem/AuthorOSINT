<h1>AuthorOSINT</h1>
  <p>Потужний OSINT-інструмент для дослідження відкритих даних</p>
</header>

<div class="container">

  <div class="section">
    <h2>🔍 Що вміє AuthorOSINT?</h2>
    <ul>
      <li><span class="icon">🌐</span><b>Загальний пошук:</b> Google + Wikipedia</li>
      <li><span class="icon">📞</span><b>Перевірка телефону:</b> геолокація, оператор, тип</li>
      <li><span class="icon">📧</span><b>Email Lookup:</b> DNS, домен, валідність</li>
      <li><span class="icon">👤</span><b>Username Scan:</b> акаунти в соцмережах (Sherlock)</li>
      <li><span class="icon">🌍</span><b>WHOIS / IP:</b> тех. дані, хостинг, країна</li>
      <li><span class="icon">🧪</span><b>Пошук субдоменів:</b> виявлення додаткових точок доступу</li>
      <li><span class="icon">🤖</span><b>AuthorAI Chat:</b> помічник із вбудованим AI</li>
    </ul>
  </div>

  <div class="section">
    <h2>🛠 Встановлення в Termux (Android)</h2>
    <p>Для користувачів <b>Termux</b> на Android виконайте наступні команди:</p>
    <div class="install-block">
termux-wake-lock<br>
pkg update && pkg upgrade -y<br>
pkg install python git curl wget whois openssl -y<br>
git clone https://github.com/VadymYem/AuthorOSINT/<br>
cd AuthorOSINT<br>
pip install --upgrade pip<br>
pip install requests beautifulsoup4 colorama phonenumbers python-whois<br>
pip install "googlesearch-python" wikipedia-api email_validator dnspython sherlock-project<br>
pip install huggingface_hub ipinfo<br>
python3 ost.py<br>
    </div>
  </div>

  <div class="section">
    <h2>💻 Встановлення в Linux (Ubuntu/Debian)</h2>
    <p>Для десктопних ОС Linux використовуйте <code>apt</code>:</p>
    <div class="install-block">
sudo apt update && sudo apt upgrade -y<br>
sudo apt install python3 git curl wget whois openssl -y<br>
git clone https://github.com/VadymYem/AuthorOSINT/<br>
cd AuthorOSINT<br>
pip install --upgrade pip<br>
pip install requests beautifulsoup4 colorama phonenumbers python-whois<br>
pip install "googlesearch-python" wikipedia-api email_validator dnspython sherlock-project<br>
pip install huggingface_hub ipinfo<br>
python3 ost.py<br>
    </div>
  </div>

  <div class="section">
    <h2>📦 Додатково: Встановлення Sherlock вручну</h2>
    <p>Якщо Sherlock не встановився автоматично, встановіть його вручну:</p>
    <div class="install-block">
git clone https://github.com/sherlock-project/sherlock.git
cd sherlock
python -m pip install -r requirements.txt
cd ..
    </div>
  </div>

  <div class="section">
    <h2>📚 Вимоги</h2>
    <ul>
      <li>Python 3.8–3.11</li>
      <li>Права на встановлення пакетів</li>
      <li>Інтернет-з'єднання</li>
    </ul>
  </div>

  <div class="section">
    <h2>🌟 Підтримка</h2>
    <p>Проєкт створено <b>AuthorChe</b>. Якщо бажаєш підтримати:</p>
    <li><a class="button" href="https://authorche.pp.ua/os.html">Вебсайт проекту</a><br></li>
    <li><a class="button" href="https://authorche.pp.ua/donate.html">Задонатити 💌</a><br></li>
    <li><a class="button" href="https://authorche.pp.ua">Вебсайт автора</a><br><br></li>
  </div>

</div>

<footer>
  © 2025 AuthorOSINT by AuthorChe | Створено з ❤️ для OSINT-дослідників
</footer>
