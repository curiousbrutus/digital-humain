# Digital Humain - Masaüstü Otomasyonu için Yapay Zeka Aracı

> 🇹🇷 **Yeni Başlayanlar İçin Türkçe Kılavuz**
> 
> Bu dokümantasyon, programlamaya yeni başlayanlar için hazırlanmıştır. Her adımı detaylı olarak açıklayacağız.

## 📚 İçindekiler

- [Digital Humain Nedir?](#digital-humain-nedir)
- [Ne İşe Yarar?](#ne-i̇şe-yarar)
- [Özellikler](#özellikler)
- [Başlamadan Önce](#başlamadan-önce)
- [Kurulum Adımları](#kurulum-adımları)
- [Proje Yapısı](#proje-yapısı)
- [İlk Kullanım](#i̇lk-kullanım)
- [Grafiksel Arayüz](#grafiksel-arayüz)
- [Örnek Kullanımlar](#örnek-kullanımlar)
- [Ayarlar](#ayarlar)
- [Sık Karşılaşılan Sorunlar](#sık-karşılaşılan-sorunlar)
- [Temel Kavramlar](#temel-kavramlar)

---

## 🤖 Digital Humain Nedir?

**Digital Humain**, bilgisayarınızdaki programları otomatik olarak kontrol edebilen bir yapay zeka sistemidir. Ekranınızı görebilir, düğmelere tıklayabilir, metin yazabilir ve sizin yerinize tekrarlayan işleri yapabilir.

### Basit Bir Örnekle

Diyelim ki her gün aynı Excel dosyasını açıp, belirli hücrelere veri giriyorsunuz. Digital Humain'e "Excel'i aç ve bu verileri gir" dediğinizde, o bunu otomatik olarak yapar.

## 🎯 Ne İşe Yarar?

Digital Humain şu alanlarda size yardımcı olabilir:

- **İş Yazılımları**: HBYS, muhasebe programları gibi kurumsal yazılımları otomatik kullanma
- **Veri Girişi**: Form doldurma, veri aktarma gibi tekrarlayan işleri otomatikleştirme
- **Raporlama**: Düzenli raporları otomatik oluşturma
- **Test İşlemleri**: Yazılım testlerini otomatik yapma
- **Ofis Görevleri**: Word, Excel gibi programlarda rutin işleri otomatikleştirme

## ✨ Özellikler

### Temel Özellikler

- 🤖 **Yapay Zeka Ajanları**: Farklı görevler için özelleşmiş yapay zeka asistanları
- 👁️ **Ekran Görme Yeteneği**: Yapay zeka ekranınızı görebilir ve neyin nerede olduğunu anlayabilir
- 🔒 **Veri Gizliliği**: Tüm işlemler bilgisayarınızda yapılır, verileriniz dışarı çıkmaz
- 🛠️ **Araç Sistemi**: Dosya okuma, yazma gibi farklı işlevler için hazır araçlar
- 🧠 **Akıllı Karar Verme**: Durumu analiz eder, ne yapacağına karar verir ve işlemi gerçekleştirir
- 🎬 **Öğrenme Özelliği**: Yaptığınız işlemleri kaydedip daha sonra tekrar edebilir
- 🎨 **Görsel Göstergeler**: Agent ne yapıyor görmek için ekranda renkli işaretler
- 🚀 **Otomatik Uygulama Bulma**: Masaüstünüzdeki programları otomatik bulur ve açar

### Gelişmiş Özellikler

- 🏗️ **Hiyerarşik Planlama**: Büyük görevleri küçük parçalara böler ve adım adım yapar
- 🔄 **Otomatik Hata Düzeltme**: Bir hata olursa tekrar deneyerek düzeltmeye çalışır
- 🛡️ **Güvenlik**: Hassas verilerinizi korur
- ⚡ **Hızlı Çalışma**: Akıllı önbellek sistemi ile daha hızlı çalışır
- 📊 **Kayıt Tutma**: Ne yaptığının detaylı kaydını tutar

## 📋 Başlamadan Önce

### Gerekli Donanım

Digital Humain'i çalıştırmak için bilgisayarınızda şu özellikler olmalı:

| Bellek (RAM) | Ekran Kartı | Tavsiye Edilen Model | Kullanım |
|--------------|-------------|----------------------|----------|
| **8GB** | Yok | Hafif modeller (moondream, llama3.2:1b) | Basit görevler |
| **16GB** | 2-4GB | Orta modeller (llama3.2:3b) | Çoğu görev için yeterli |
| **32GB** | 8GB+ | Büyük modeller (llama3.2-vision) | Gelişmiş kullanım |

**Not**: 8GB RAM'li bir bilgisayar temel görevler için yeterlidir.

### Gerekli Yazılımlar

1. **Python 3.9 veya üzeri**: Programın çalışması için gerekli
2. **Ollama**: Yapay zeka modellerini bilgisayarınızda çalıştırır (ücretsiz)
3. **Tesseract OCR**: Ekrandaki metinleri okur (ücretsiz)

### İşletim Sistemi Desteği

| İşletim Sistemi | Durum | Notlar |
|-----------------|-------|--------|
| **Windows** | ✅ Tam Destek | Windows 10/11 |
| **Linux** | ✅ Tam Destek | Ubuntu 22.04+ test edildi |
| **macOS** | ✅ Destekleniyor | Ek kurulum gerekebilir |

---

## 🚀 Kurulum Adımları

Her adımı sırasıyla takip edin. Bir sorun çıkarsa [Sık Karşılaşılan Sorunlar](#sık-karşılaşılan-sorunlar) bölümüne bakın.

### Adım 1: Python Kurulumu

**Python nedir?** Digital Humain Python programlama dili ile yazılmıştır. Python'u bilgisayarınıza kurmanız gerekir.

#### Windows için:
```
1. https://www.python.org/downloads/ adresine gidin
2. "Download Python" butonuna tıklayın
3. İndirilen dosyayı çalıştırın
4. MUTLAKA "Add Python to PATH" kutucuğunu işaretleyin
5. "Install Now" butonuna tıklayın
```

#### Linux için:
```bash
# Terminal'i açın ve şu komutu yazın:
sudo apt update
sudo apt install python3 python3-pip
```

#### macOS için:
```bash
# Terminal'i açın ve şu komutu yazın:
brew install python3
```

**Kontrol**: Python'un doğru kurulup kurulmadığını kontrol etmek için terminal/komut istemi'ni açın ve şunu yazın:
```bash
python --version
```
Çıktı: `Python 3.9.0` veya üzeri bir sürüm görmelisiniz.

### Adım 2: Digital Humain'i İndirin

**Git nedir?** Kod projelerini indirmek ve yönetmek için kullanılan bir araçtır.

#### Git Kurulumu:

**Windows için:** https://git-scm.com/download/win adresinden indirip kurun.

**Linux için:**
```bash
sudo apt install git
```

**macOS için:**
```bash
brew install git
```

#### Projeyi İndirin:

Terminal veya Komut İstemi'ni açın ve şu komutları yazın:

```bash
# Projeyi indirin
git clone https://github.com/curiousbrutus/digital-humain.git

# İndirilen klasöre girin
cd digital-humain
```

**Ne yaptık?** Digital Humain'in tüm dosyalarını bilgisayarınıza kopyaladık.

### Adım 3: Gerekli Kütüphaneleri Kurun

**Kütüphane nedir?** Python programlarının ihtiyaç duyduğu ek kod parçalarıdır.

```bash
# digital-humain klasöründeyken şu komutu çalıştırın:
pip install -r requirements.txt
```

**Bu işlem biraz zaman alabilir** (5-10 dakika). İnternet bağlantınızın iyi olması gerekir.

**Sorun çıkarsa:**
```bash
# Windows'ta şunu deneyin:
python -m pip install -r requirements.txt

# Veya:
pip3 install -r requirements.txt
```

### Adım 4: Tesseract OCR Kurulumu

**Tesseract nedir?** Ekrandaki metinleri okuyabilen bir araçtır (örneğin, bir düğmenin üzerindeki yazıyı).

#### Windows için:
```
1. https://github.com/UB-Mannheim/tesseract/wiki adresine gidin
2. En son sürümü indirin (örn: tesseract-ocr-w64-setup-5.3.1.exe)
3. İndirilen dosyayı çalıştırıp kurun
4. Kurulum sırasında "Additional language data" seçeneğinden Türkçe'yi seçin
```

#### Linux için:
```bash
sudo apt install tesseract-ocr tesseract-ocr-tur
```

#### macOS için:
```bash
brew install tesseract
```

**Kontrol**: Tesseract'ın kurulduğunu kontrol edin:
```bash
tesseract --version
```

### Adım 5: Linux için Ek Kurulum (Sadece Linux Kullanıcıları)

Linux kullanıyorsanız ekran görüntüsü için ek araçlar gerekir:

```bash
# Ekran görüntüsü araçları
sudo apt install scrot gnome-screenshot

# PyAutoGUI için gerekli kütüphaneler
sudo apt install python3-tk python3-dev

# X11 kütüphaneleri
sudo apt install python3-xlib
```

### Adım 6: Ollama Kurulumu

**Ollama nedir?** Yapay zeka modellerini bilgisayarınızda çalıştırmanıza yarayan ücretsiz bir programdır. Bu sayede verileriniz bilgisayarınızdan çıkmaz.

#### Ollama'yı Kurun:

**Linux/macOS için:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows için:**
```
1. https://ollama.ai/download adresine gidin
2. Windows sürümünü indirin
3. İndirilen dosyayı çalıştırıp kurun
```

#### Ollama'yı Başlatın:

```bash
# Ollama servisini başlatın
ollama serve
```

**Bu komutu çalıştırdıktan sonra terminal penceresi açık kalmalıdır.** Yeni bir terminal penceresi açın ve devam edin.

#### Yapay Zeka Modelini İndirin:

**Moondream (Tavsiye Edilen - Hafif)**

8GB RAM'li bilgisayarlar için idealdir:

```bash
ollama pull moondream
```

**Açıklama**: Moondream, sadece 1.7GB boyutunda ve ekranı görebilen hafif bir modeldir.

**Diğer Model Seçenekleri:**

```bash
# Sadece metin için (daha küçük, daha hızlı)
ollama pull llama3.2:1b

# Daha güçlü ekran görme (4GB gerektirir)
ollama pull llama3.2-vision

# Daha büyük metin modeli (daha akıllı)
ollama pull llama3.2:3b
```

**Model Karşılaştırması:**

| Model | Boyut | Hız | Kullanım |
|-------|-------|-----|----------|
| **llama3.2:1b** | 700MB | ⚡ Çok Hızlı | Basit metin işleme |
| **moondream** | 1.7GB | ⚡ Hızlı | Ekran görme + metin (TAVSİYE) |
| **llama3.2:3b** | 2GB | 🚀 Orta | Daha akıllı işlemler |
| **llama3.2-vision** | 4GB | 🚀 Orta | Gelişmiş ekran analizi |

**Test**: Modelin çalışıp çalışmadığını test edin:
```bash
ollama run moondream "Merhaba, nasılsın?"
```

### Adım 7: Ayar Dosyasını Düzenleyin

**Ayar dosyası nedir?** Digital Humain'in nasıl çalışacağını belirten dosyadır.

```bash
# Ayar dosyasını açın
# Windows'ta:
notepad config/config.yaml

# Linux/macOS'ta:
nano config/config.yaml
```

**Önemli Ayarlar:**

```yaml
llm:
  provider: ollama          # Ollama kullanıyoruz
  model: moondream          # Hangi model kullanılacak
  base_url: http://localhost:11434
  temperature: 0.7
  timeout: 300
```

**temperature nedir?** Yapay zekanın ne kadar yaratıcı olacağını belirler:
- 0.0 = Hep aynı cevapları verir (tekrarlayan görevler için)
- 0.7 = Dengeli (tavsiye edilen)
- 1.0 = Daha yaratıcı ama bazen beklenmedik

Dosyayı kaydedin ve kapatın.

---

## 📁 Proje Yapısı

Digital Humain projesinin klasörleri ve ne işe yaradıkları:

```
digital-humain/
│
├── 📁 digital_humain/          # Ana program kodları
│   │
│   ├── 📁 core/                # Temel yapı taşları
│   │   ├── agent.py           # Agent'ların ana yapısı
│   │   ├── engine.py          # Agent'ları çalıştıran motor
│   │   └── llm.py             # Yapay zeka ile iletişim
│   │
│   ├── 📁 vlm/                 # Görme özellikleri
│   │   ├── screen_analyzer.py # Ekranı analiz eder
│   │   ├── actions.py         # Tıklama, yazma gibi işlemler
│   │   └── overlay.py         # Ekranda görsel göstergeler
│   │
│   ├── 📁 agents/              # Farklı amaçlar için agent'lar
│   │   ├── automation_agent.py    # Masaüstü otomasyonu agent'ı
│   │   └── hierarchical_planning.py # Büyük görevleri planlayan agent
│   │
│   ├── 📁 tools/               # Agent'ların kullandığı araçlar
│   │   ├── file_tools.py      # Dosya okuma, yazma
│   │   ├── system_tools.py    # Sistem komutları
│   │   └── browser_tools.py   # Web tarayıcı işlemleri
│   │
│   ├── 📁 memory/              # Öğrenme ve hafıza sistemi
│   │   ├── episodic.py        # Geçmiş deneyimleri hatırlar
│   │   └── demonstration.py   # Kullanıcı gösterilerini kaydeder
│   │
│   ├── 📁 orchestration/       # Birden fazla agent koordinasyonu
│   │   ├── coordinator.py     # Agent'ları yönetir
│   │   ├── registry.py        # Agent kayıt sistemi
│   │   └── memory.py          # Paylaşılan hafıza
│   │
│   └── 📁 utils/               # Yardımcı araçlar
│       ├── logger.py          # Kayıt sistemi
│       └── config.py          # Ayar yönetimi
│
├── 📁 config/                  # Ayar dosyaları
│   └── config.yaml            # Ana ayar dosyası
│
├── 📁 examples/                # Örnek kullanımlar
│   ├── simple_automation.py   # Basit otomasyon örneği
│   ├── multi_agent_orchestration.py  # Çoklu agent örneği
│   └── memory_demo.py         # Hafıza özellikleri örneği
│
├── 📁 tests/                   # Test dosyaları
│   ├── unit/                  # Birim testler
│   └── integration/           # Entegrasyon testleri
│
├── 📁 docs/                    # Dokümantasyon
│
├── 📄 gui_main.py              # Ana grafiksel arayüz
├── 📄 gui_letta.py             # Gelişmiş arayüz
├── 📄 requirements.txt         # Gerekli kütüphaneler listesi
└── 📄 README.md                # Bu dosya (İngilizce)
```

### Klasörlerin Detaylı Açıklaması

#### 🤖 `core/` - Temel Sistem

Bu klasör, Digital Humain'in beyni gibidir. Agent'ların nasıl çalışacağını, yapay zeka ile nasıl konuşacağını belirler.

- **agent.py**: Tüm agent'ların temel yapısı. Bir agent'ın mutlaka "gözlem yap", "düşün", "hareket et" yetenekleri olur.
- **engine.py**: Agent'ları çalıştıran motor. Bir görev verildiğinde agent'ı başlatır ve tamamlanana kadar çalıştırır.
- **llm.py**: Yapay zeka modelleri (Ollama, OpenRouter) ile konuşmayı sağlar.

#### 👁️ `vlm/` - Görme Özellikleri

VLM = Vision Language Model (Görsel Dil Modeli). Bu klasör, agent'ın ekranı görmesini ve anlamsını sağlar.

- **screen_analyzer.py**: Ekranın fotoğrafını çeker ve yapay zekaya "bu ekranda ne var?" diye sorar.
- **actions.py**: Mouse'u hareket ettirir, tıklar, klavyeden yazar.
- **overlay.py**: Ekranda renkli işaretler gösterir (agent'ın nereye tıkladığını görmeniz için).

#### 🤖 `agents/` - Özelleşmiş Agent'lar

Farklı işler için hazırlanmış agent'lar burada.

- **automation_agent.py**: Masaüstü programlarını otomatik kullanır.
- **hierarchical_planning.py**: Büyük görevleri küçük adımlara böler ve planlar.

#### 🛠️ `tools/` - Araçlar

Agent'ların işlerini yapması için kullandıkları araçlar.

- **file_tools.py**: Dosya okuma, yazma, listeleme
- **system_tools.py**: Program açma, komut çalıştırma
- **browser_tools.py**: Web tarayıcıda arama yapma, sayfa açma

#### 🧠 `memory/` - Hafıza Sistemi

Agent'ların öğrenmesini ve hatırlamasını sağlar.

- **episodic.py**: Geçmişte ne yaptığını hatırlar ("Daha önce bu ekranı gördüm, şunu yapmıştım")
- **demonstration.py**: Sizin yaptığınız işlemleri kaydeder ve tekrar eder

#### 🎭 `orchestration/` - Orkestrasyon

Birden fazla agent'ı koordine eder.

- **coordinator.py**: "Bu görevi sen yap, şunu da sen yap" diye agent'lara görev dağıtır
- **registry.py**: Hangi agent'lar mevcut, ne yapabiliyorlar bilgisini tutar
- **memory.py**: Agent'ların birbirleriyle bilgi paylaşmasını sağlar

---

## 🎮 İlk Kullanım

### Test: Kurulum Tamamlandı mı?

Herşeyin doğru kurulup kurulmadığını test edelim:

```bash
# Ollama çalışıyor mu?
curl http://localhost:11434/api/tags

# Python ve kütüphaneler kurulu mu?
python -c "import digital_humain; print('OK')"

# Tesseract kurulu mu?
tesseract --version
```

Hepsi hatasız çalışıyorsa, kurulum tamamdır! 🎉

### Basit Bir Örnek Çalıştırın

```bash
# Basit otomasyon örneğini çalıştırın
python examples/simple_automation.py
```

Bu örnek, ekranı analiz eder ve ne gördüğünü söyler.

---

## 🖥️ Grafiksel Arayüz

Digital Humain'i kullanmanın en kolay yolu grafiksel arayüzüdür.

### Ana Arayüzü Başlatın

```bash
python gui_main.py
```

**Arayüz Açıklaması:**

1. **LLM Yapılandırma Paneli** (Sol üst)
   - **Sağlayıcı**: Ollama veya OpenRouter seçin
   - **Model**: Hangi yapay zeka modelini kullanacağınızı seçin
   - **Sağlık Göstergesi**: Yeşil nokta = bağlantı var, Kırmızı = sorun var

2. **Görev Yürütme** (Orta)
   - **Görev girişi**: Ne yapmak istediğinizi yazın
   - **Çalıştır**: Görevi başlatır
   - **Durdur**: Çalışan görevi iptal eder

3. **Kayıt Kontrolleri** (Sağ)
   - **Kaydı Başlat**: Yaptığınız işlemleri kaydeder
   - **Kaydı Durdur**: Kaydı bitirir
   - **Kaydet**: Kaydı dosyaya kaydeder
   - **Yükle**: Önceki kaydı açar
   - **Tekrarla**: Kaydı otomatik tekrar eder

4. **Yürütme Günlükleri** (Alt)
   - Agent'ın ne yaptığını gösterir

### Gelişmiş Arayüz (Letta Stili)

Daha profesyonel bir arayüz için:

```bash
python gui_letta.py
```

Bu arayüz şunları sunar:
- 🧠 **Hafıza Blokları**: Agent'ın sizi ve kendisini hatırlaması
- 📚 **Arşiv Hafızası**: Uzun süreli bilgi depolama
- 💬 **Zengin Konuşmalar**: Zaman damgalı mesajlar
- 📊 **Token İzleme**: Ne kadar bellek kullanıldığını görme

---

## 💡 Örnek Kullanımlar

### Örnek 1: Ekranı Analiz Etme

```python
from digital_humain.vlm.screen_analyzer import ScreenAnalyzer
from digital_humain.core.llm import OllamaProvider

# Ekran analizörü oluştur
vlm = OllamaProvider(model="moondream")
analyzer = ScreenAnalyzer(vlm_provider=vlm, save_screenshots=True)

# Ekranı analiz et
result = analyzer.analyze_screen("Ekranda hangi düğmeler var?")
print(result)
```

**Ne yapar?** Ekranın fotoğrafını çeker ve "hangi düğmeler var?" sorusunun cevabını verir.

### Örnek 2: Basit Otomasyon

```python
from digital_humain.core.agent import AgentConfig, AgentRole
from digital_humain.core.llm import OllamaProvider
from digital_humain.agents.automation_agent import DesktopAutomationAgent

# Agent yapılandırması
config = AgentConfig(
    name="otomasyon_agenti",
    role=AgentRole.EXECUTOR,
    max_iterations=10  # Maksimum 10 adım
)

# Agent oluştur
llm = OllamaProvider(model="moondream")
agent = DesktopAutomationAgent(config=config, llm_provider=llm)

# Görevi çalıştır
result = agent.execute("Notepad'i aç ve 'Merhaba Dünya' yaz")
print(result)
```

**Ne yapar?** Notepad programını açar ve içine "Merhaba Dünya" yazar.

### Örnek 3: Dosya İşlemleri

```python
from digital_humain.tools.file_tools import FileReadTool, FileWriteTool

# Dosya okuma
read_tool = FileReadTool()
content = read_tool.execute(path="./belgeler/notlar.txt")
print(f"Dosya içeriği: {content}")

# Dosya yazma
write_tool = FileWriteTool()
write_tool.execute(
    path="./belgeler/yeni_not.txt",
    content="Bu Digital Humain ile yazıldı!"
)
```

**Ne yapar?** Bir dosyayı okur ve yeni bir dosya oluşturur.

---

## ⚙️ Ayarlar

### Yapay Zeka Modelini Değiştirme

`config/config.yaml` dosyasını açın:

```yaml
llm:
  provider: ollama
  model: moondream    # Bunu değiştirebilirsiniz
  base_url: http://localhost:11434
  temperature: 0.7
```

**Model seçenekleri:**
- `moondream` - Hafif, ekran görme var (TAVSİYE)
- `llama3.2:1b` - Çok hafif, sadece metin
- `llama3.2:3b` - Daha akıllı, daha yavaş
- `llama3.2-vision` - Gelişmiş ekran görme

### Cloud (Bulut) Kullanımı

Bilgisayarınız yeterince güçlü değilse, internet üzerinden yapay zeka kullanabilirsiniz:

1. https://openrouter.ai adresine gidin ve kayıt olun
2. API anahtarınızı alın
3. Proje klasöründe `.env` dosyası oluşturun:

```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
```

4. `config/config.yaml` dosyasını düzenleyin:

```yaml
llm:
  provider: openrouter
  openrouter:
    base_url: https://openrouter.ai/api/v1
    api_key: ${OPENROUTER_API_KEY}
    default_model: google/gemini-2.0-flash-exp:free
```

**Ücretsiz modeller:**
- `google/gemini-2.0-flash-exp:free` - Hızlı ve akıllı
- `meta-llama/llama-3.2-11b-vision-instruct:free` - Ekran görme var
- `qwen/qwen-2.5-72b-instruct:free` - Çok akıllı

### Diğer Ayarlar

```yaml
# Agent davranışı
agent:
  max_iterations: 10          # Maksimum adım sayısı
  timeout: 300                # Zaman aşımı (saniye)

# Ekran görüntüsü
vlm:
  save_screenshots: true      # Ekran görüntülerini kaydet
  screenshot_dir: screenshots # Kaydedilecek klasör

# Kayıt sistemi
logging:
  level: INFO                 # DEBUG, INFO, WARNING, ERROR
  file: logs/digital_humain.log
```

---

## 🔧 Sık Karşılaşılan Sorunlar

### Sorun 1: "Ollama'ya bağlanılamıyor"

**Çözüm:**
```bash
# Ollama'nın çalıştığından emin olun
ollama serve

# Başka bir terminalde test edin
curl http://localhost:11434/api/tags
```

Eğer hata veriyorsa, Ollama'yı yeniden kurun.

### Sorun 2: "Tesseract bulunamadı"

**Çözüm:**

**Windows:**
1. Tesseract'ı yeniden kurun
2. Çevre değişkenlerine PATH ekleyin:
   - Bilgisayarım → Özellikler → Gelişmiş sistem ayarları
   - Çevre Değişkenleri → Path → Düzenle
   - `C:\Program Files\Tesseract-OCR` ekleyin

**Linux:**
```bash
sudo apt install tesseract-ocr
```

### Sorun 3: "PyAutoGUI ekran görüntüsü alamıyor" (Linux)

**Çözüm:**
```bash
# Gerekli araçları kurun
sudo apt install scrot gnome-screenshot python3-tk
```

### Sorun 4: "ModuleNotFoundError: No module named 'digital_humain'"

**Çözüm:**
```bash
# Doğru klasörde olduğunuzdan emin olun
cd /path/to/digital-humain

# Kütüphaneleri yeniden kurun
pip install -r requirements.txt

# Veya geliştirici modunda kurun
pip install -e .
```

### Sorun 5: "Bellek hatası / Out of Memory"

**Çözüm:**

Daha küçük bir model kullanın:

```bash
# Moondream yerine daha küçük model
ollama pull llama3.2:1b

# config.yaml'de değiştirin
model: llama3.2:1b
```

### Sorun 6: "Agent hiçbir şey yapmıyor"

**Çözüm:**

1. Görevi daha açık yazın:
   - ❌ Kötü: "bir şeyler yap"
   - ✅ İyi: "Notepad'i aç ve 'test' yaz"

2. Loglara bakın:
```bash
# Detaylı log için
python gui_main.py --log-level DEBUG
```

3. Model çalışıyor mu test edin:
```bash
ollama run moondream "Merhaba"
```

### Sorun 7: GUI açılmıyor

**Çözüm:**

**Linux:**
```bash
# Tkinter kurulu mu?
sudo apt install python3-tk

# Display ayarları
echo $DISPLAY  # Boş olmamalı
export DISPLAY=:0
```

**Windows:**
Python'u yeniden kurun ve "tcl/tk" seçeneğini işaretleyin.

---

## 📖 Temel Kavramlar

### Agent (Ajan) Nedir?

**Agent**, belirli bir görevi yapmak için programlanmış akıllı bir asistantır. Bir agent:
1. **Gözlemler**: Ekrana bakar, durum analizi yapar
2. **Düşünür**: "Ne yapmam gerekiyor?" diye karar verir
3. **Harekete Geçer**: Kararını uygular (tıklar, yazar, vb.)
4. **Tekrar eder**: Görev bitene kadar döngü devam eder

**Örnek:** "Excel'i aç ve A1 hücresine 100 yaz" görevi için agent:
- Gözlem: Masaüstünü görür
- Düşünme: "Excel'i bulmam lazım"
- Hareket: Excel'e çift tıklar
- Gözlem: Excel açıldı
- Düşünme: "A1 hücresine tıklamam lazım"
- Hareket: A1'e tıklar
- ... (devam eder)

### VLM (Vision Language Model) Nedir?

**VLM**, hem görebilen hem de dili anlayan yapay zeka modelidir. Normal yapay zeka sadece metin anlayabilirken, VLM ekran görüntülerine bakıp "bu bir düğme", "burada bir form var" gibi analiz yapabilir.

**Moondream** gibi modeller VLM'dir.

### Tool (Araç) Nedir?

**Tool**, agent'ın kullanabileceği özel bir yetenektir. Örneğin:
- FileReadTool: Dosya okuma yeteneği
- FileWriteTool: Dosya yazma yeteneği
- BrowserTool: Web tarayıcı kullanma yeteneği

Agent'lar, görevlerini yapmak için bu araçları kullanır.

### Orchestration (Orkestrasyon) Nedir?

**Orchestration**, birden fazla agent'ın koordineli çalışmasıdır. Büyük bir görev, küçük parçalara bölünür ve her parça bir agent'a verilir.

**Örnek:** "İnternetten veri topla, Excel'e aktar ve rapor oluştur" görevi:
- **Agent 1**: Web'den veri toplar
- **Agent 2**: Verileri Excel'e yazar
- **Agent 3**: Rapor oluşturur
- **Coordinator**: Üç agent'ı koordine eder

### Memory (Hafıza) Nedir?

**Memory**, agent'ın geçmiş deneyimlerini hatırlamasıdır:

- **Episodic Memory**: "Geçen sefer bu ekranda şunu yaptım" gibi hatıralar
- **Demonstration Memory**: Sizin yaptığınız işlemleri kaydeder
- **Shared Memory**: Agent'lar arasında paylaşılan bilgi

---

## 🎓 İleri Seviye Kullanım

### Kendi Agent'ınızı Yazma

```python
from digital_humain.core.agent import BaseAgent, AgentConfig

class BenimAgentim(BaseAgent):
    """Özel agent sınıfı"""
    
    def reason(self, state, observation):
        """Ne yapacağına karar verir"""
        # Burada düşünme mantığını yazın
        return "yapılacak_işlem"
    
    def act(self, state, reasoning):
        """Kararı uygular"""
        # Burada hareketi gerçekleştirin
        return "işlem_sonucu"

# Kullanım
config = AgentConfig(name="benim_agentim", role=AgentRole.EXECUTOR)
agent = BenimAgentim(config=config, llm_provider=llm)
```

### Kendi Tool'unuzu Yazma

```python
from digital_humain.tools.base import BaseTool, ToolMetadata, ToolResult

class HesapMakinesiTool(BaseTool):
    """Basit hesaplama aracı"""
    
    def get_metadata(self):
        return ToolMetadata(
            name="hesap_makinesi",
            description="İki sayıyı toplar",
            parameters=[
                {"name": "sayi1", "type": "number"},
                {"name": "sayi2", "type": "number"}
            ]
        )
    
    def execute(self, sayi1, sayi2):
        sonuc = sayi1 + sayi2
        return ToolResult(
            success=True,
            result=sonuc,
            message=f"{sayi1} + {sayi2} = {sonuc}"
        )

# Kullanım
tool = HesapMakinesiTool()
result = tool.execute(sayi1=5, sayi2=3)
print(result.result)  # 8
```

---

## 🔒 Güvenlik ve Gizlilik

Digital Humain, gizliliğinizi ciddiye alır:

- ✅ **Varsayılan olarak yerel çalışma**: Tüm işlemler bilgisayarınızda yapılır
- ✅ **Veri dışarı çıkmaz**: Ollama kullandığınızda hiçbir veri internete gitmez
- ✅ **Şifre güvenliği**: API anahtarları `.env` dosyasında saklanır (asla kod içinde değil)
- ✅ **İsteğe bağlı bulut**: Cloud kullanımı tamamen isteğe bağlıdır

**Öneriler:**
1. Hassas verilerle çalışıyorsanız mutlaka Ollama kullanın
2. `.env` dosyasını asla kimseyle paylaşmayın
3. API anahtarlarınızı düzenli değiştirin

---

## 🤝 Katkıda Bulunma

Digital Humain açık kaynaklı bir projedir ve katkılarınızı bekliyoruz!

**Nasıl katkıda bulunabilirsiniz:**

1. **Hata Bildirimi**: Bulduğunuz hataları GitHub Issues'da bildirin
2. **Özellik Önerisi**: Yeni fikirlerinizi paylaşın
3. **Kod Katkısı**: Pull request gönderin
4. **Dokümantasyon**: Dökümantasyonu geliştirin veya Türkçeleştirin
5. **Örnek Oluşturma**: Yeni kullanım örnekleri ekleyin

---

## 📞 Destek

**Yardıma mı ihtiyacınız var?**

- 🐛 **Hata bildirimi**: [GitHub Issues](https://github.com/curiousbrutus/digital-humain/issues)
- 💬 **Sorular**: GitHub Discussions bölümünü kullanın
- 📖 **Dokümantasyon**: `docs/` klasöründeki detaylı dokümanlara bakın

---

## 📚 Ek Kaynaklar

### Öğrenme Kaynakları

- **Python Öğrenme**: https://python.org.tr
- **Yapay Zeka Temelleri**: https://www.youtube.com/watch?v=aircAruvnKk (Türkçe altyazılı)
- **Git Öğrenme**: https://www.youtube.com/watch?v=3qf6bX3g-a4 (Türkçe)

### İlgili Projeler

- **LangChain**: https://python.langchain.com/
- **Ollama**: https://ollama.ai/
- **PyAutoGUI**: https://pyautogui.readthedocs.io/

---

## 📝 Lisans

[OpenSource 2.0]

---

## 🌟 Son Notlar

**Tebrikler!** Digital Humain'i kurup kullanmaya başladınız. 

**İlk adımlar:**
1. ✅ Kurulumu tamamladınız
2. ✅ Basit örnekleri çalıştırdınız
3. ✅ GUI'yi keşfettiniz

**Bundan sonra:**
- `examples/` klasöründeki örnekleri inceleyin
- Kendi görevlerinizi oluşturmaya başlayın
- Sorunla karşılaşırsanız bu rehbere geri dönün

**Unutmayın:** Programlama öğrenmek zaman alır. Hata yapmaktan korkmayın, her hata bir öğrenme fırsatıdır! 🚀

---


📅 **Son güncelleme**: Aralık 2025

💝 **Topluluk katkılarıyla geliştirilmiştir**
