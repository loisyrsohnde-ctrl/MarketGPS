"""
Company Information Database
Contains descriptions and sector info for major companies
"""

# Company descriptions (brief, one paragraph)
COMPANY_DESCRIPTIONS = {
    # ============================================
    # US TECH
    # ============================================
    "AAPL": "Apple Inc. est le leader mondial de l'électronique grand public, créateur de l'iPhone, iPad, Mac et Apple Watch. L'entreprise développe également des services numériques (App Store, Apple Music, iCloud) représentant une part croissante de ses revenus. Fondée en 1976, Apple est connue pour son design innovant et son écosystème intégré.",
    
    "MSFT": "Microsoft Corporation est le géant mondial du logiciel, créateur de Windows et de la suite Office. L'entreprise s'est transformée sous Satya Nadella pour devenir un leader du cloud computing avec Azure, rivalisant avec Amazon AWS. Microsoft possède également LinkedIn, GitHub et la division gaming Xbox.",
    
    "GOOGL": "Alphabet Inc. (Google) domine le marché de la recherche en ligne et de la publicité digitale. L'entreprise possède YouTube, Android, Google Cloud, et investit massivement dans l'intelligence artificielle. Ses revenus proviennent principalement de la publicité ciblée.",
    
    "AMZN": "Amazon.com est le leader mondial du e-commerce et du cloud computing (AWS). Fondée par Jeff Bezos en 1994, l'entreprise s'est diversifiée dans le streaming (Prime Video), les appareils connectés (Alexa), et la logistique. AWS génère la majorité des profits du groupe.",
    
    "META": "Meta Platforms (anciennement Facebook) est le géant des réseaux sociaux avec Facebook, Instagram, WhatsApp et Messenger. L'entreprise investit massivement dans le métavers et la réalité virtuelle. Ses revenus proviennent quasi exclusivement de la publicité.",
    
    "NVDA": "NVIDIA Corporation est le leader mondial des processeurs graphiques (GPU). Initialement focalisé sur le gaming, NVIDIA domine aujourd'hui le marché des puces pour l'intelligence artificielle et les data centers. La demande explosive pour l'IA a propulsé sa valorisation.",
    
    "TSLA": "Tesla Inc. est le pionnier et leader des véhicules électriques, fondé par Elon Musk. L'entreprise produit également des batteries, des panneaux solaires et développe la conduite autonome. Tesla a révolutionné l'industrie automobile et inspiré la transition électrique.",
    
    # ============================================
    # US FINANCE
    # ============================================
    "JPM": "JPMorgan Chase est la plus grande banque américaine par actifs. Elle opère dans la banque d'investissement, la gestion d'actifs, et la banque de détail. Dirigée par Jamie Dimon, JPM est considérée comme la banque la plus influente de Wall Street.",
    
    "V": "Visa Inc. est le leader mondial des paiements électroniques. Son réseau traite des milliards de transactions chaque année, connectant consommateurs, commerçants et institutions financières. Visa profite de la digitalisation croissante des paiements.",
    
    "MA": "Mastercard Incorporated est le deuxième réseau mondial de paiements électroniques. L'entreprise facilite les transactions entre banques, commerçants et consommateurs dans plus de 200 pays. Elle investit dans les fintechs et les paiements sans contact.",
    
    # ============================================
    # FRANCE
    # ============================================
    "MC": "LVMH Moët Hennessy Louis Vuitton est le leader mondial du luxe, regroupant 75 maisons prestigieuses dont Louis Vuitton, Dior, Tiffany, Moët & Chandon et Hennessy. Fondé par Bernard Arnault, le groupe français domine les secteurs de la mode, des spiritueux, de la joaillerie et des cosmétiques.",
    
    "OR": "L'Oréal est le numéro un mondial des cosmétiques avec un portefeuille de 36 marques dont L'Oréal Paris, Lancôme, Maybelline et Kérastase. Présent dans 150 pays, le groupe français investit massivement dans la beauté tech et les produits durables.",
    
    "SAN": "Sanofi est un leader mondial de la santé, spécialisé dans les vaccins, les maladies rares et l'immunologie. Ce groupe pharmaceutique français développe des traitements innovants et possède une forte présence dans les médicaments grand public avec Doliprane et Opella.",
    
    "TTE": "TotalEnergies est une major pétrolière et gazière française en pleine transformation vers les énergies renouvelables. Le groupe investit massivement dans le solaire, l'éolien et les biocarburants tout en maintenant ses activités traditionnelles dans les hydrocarbures.",
    
    "BNP": "BNP Paribas est la première banque de la zone euro par actifs. Le groupe français opère dans la banque de détail, la banque d'investissement et la gestion d'actifs dans plus de 65 pays. BNP est un acteur majeur du financement de la transition énergétique.",
    
    "AI": "Air Liquide est le leader mondial des gaz industriels et médicaux. L'entreprise française fournit oxygène, azote et hydrogène à l'industrie et aux hôpitaux. Air Liquide est un acteur clé de la transition énergétique avec l'hydrogène vert.",
    
    "CAP": "Capgemini est un leader mondial du conseil et des services informatiques. Le groupe français accompagne les entreprises dans leur transformation digitale, l'intelligence artificielle et le cloud. Présent dans 50 pays avec 350 000 collaborateurs.",
    
    "ORA": "Orange est le premier opérateur télécom en France et un acteur majeur en Europe et en Afrique. Le groupe propose des services mobiles, internet fixe et des solutions pour les entreprises. Orange investit dans la 5G et la cybersécurité.",
    
    # ============================================
    # GERMANY
    # ============================================
    "SAP": "SAP SE est le leader mondial des logiciels de gestion d'entreprise (ERP). L'entreprise allemande équipe 87% des entreprises du Fortune 500. SAP accélère sa transition vers le cloud avec S/4HANA et développe des solutions d'intelligence artificielle.",
    
    "SIE": "Siemens AG est un conglomérat industriel allemand leader dans l'automatisation, la digitalisation et l'électrification. L'entreprise fournit des solutions pour l'industrie, les infrastructures, les transports et la santé. Siemens est pionnier de l'Industrie 4.0.",
    
    "ALV": "Allianz SE est le premier assureur européen et un leader mondial de la gestion d'actifs via PIMCO. Le groupe allemand propose assurances vie, dommages et santé dans plus de 70 pays. Allianz gère plus de 2 000 milliards d'euros d'actifs.",
    
    "BMW": "BMW AG (Bayerische Motoren Werke) est le constructeur allemand de voitures premium et de motos. Le groupe possède les marques BMW, MINI et Rolls-Royce. BMW investit massivement dans les véhicules électriques et la conduite autonome.",
    
    "DTE": "Deutsche Telekom est le premier opérateur télécom européen et propriétaire de T-Mobile US. Le groupe allemand fournit services mobiles, internet et solutions IT. La croissance de T-Mobile aux États-Unis est le principal moteur du groupe.",
    
    "VOW3": "Volkswagen AG est le premier constructeur automobile mondial par volume. Le groupe allemand possède VW, Audi, Porsche, Lamborghini et Bentley. Volkswagen accélère son offensive électrique avec la plateforme MEB et investit dans les batteries.",
    
    "ADS": "Adidas AG est le deuxième équipementier sportif mondial derrière Nike. La marque allemande aux trois bandes équipe athlètes et passionnés de sport. Adidas mise sur le lifestyle, le développement durable et les collaborations avec des célébrités.",
    
    # ============================================
    # UK
    # ============================================
    "SHEL": "Shell plc est une major pétrolière et gazière anglo-néerlandaise, l'une des plus grandes entreprises énergétiques mondiales. Shell investit dans la transition énergétique, les énergies renouvelables et l'hydrogène tout en maintenant sa production d'hydrocarbures.",
    
    "AZN": "AstraZeneca est un groupe pharmaceutique anglo-suédois spécialisé en oncologie, maladies cardiovasculaires et respiratoires. Connu pour son vaccin COVID-19, AstraZeneca développe des traitements innovants et des thérapies cellulaires.",
    
    "HSBC": "HSBC Holdings est l'une des plus grandes banques mondiales, avec une forte présence en Asie. La banque britannique offre services bancaires, gestion de patrimoine et banque d'investissement. HSBC recentre ses activités sur l'Asie, son marché le plus rentable.",
    
    "ULVR": "Unilever plc est un géant anglo-néerlandais des biens de consommation. Le groupe possède des marques emblématiques comme Dove, Lipton, Ben & Jerry's et Axe. Unilever s'engage pour le développement durable et la réduction de son empreinte environnementale.",
    
    "BP": "BP plc (British Petroleum) est une major pétrolière britannique en transformation vers les énergies bas carbone. Le groupe investit dans l'éolien offshore, le solaire et les biocarburants tout en réduisant progressivement sa production pétrolière.",
    
    "GSK": "GSK plc (GlaxoSmithKline) est un groupe pharmaceutique britannique spécialisé dans les vaccins, les médicaments et la santé grand public. Suite à la scission de sa division Consumer Health (Haleon), GSK se concentre sur la biopharmacie.",
    
    "RIO": "Rio Tinto est l'un des plus grands groupes miniers mondiaux, extrayant minerai de fer, aluminium, cuivre et diamants. L'entreprise anglo-australienne fournit les matières premières essentielles à l'industrie mondiale et à la transition énergétique.",
    
    "BARC": "Barclays plc est une banque universelle britannique avec des activités en banque de détail, cartes de crédit et banque d'investissement. Barclays est particulièrement forte aux États-Unis dans le trading et la banque d'affaires.",
    
    "VOD": "Vodafone Group est un opérateur télécom britannique présent en Europe et en Afrique. Le groupe fournit services mobiles, internet fixe et solutions IoT. Vodafone restructure son portefeuille en cédant certains marchés européens.",
    
    # ============================================
    # SOUTH AFRICA
    # ============================================
    "NPN": "Naspers est un groupe sud-africain de médias et d'internet, principal actionnaire de Tencent (Chine). Via Prosus, Naspers investit dans les technologies de livraison, fintech et e-commerce. La participation dans Tencent représente l'essentiel de sa valeur.",
    
    "MTN": "MTN Group est le premier opérateur télécom africain, présent dans 19 pays d'Afrique et du Moyen-Orient. MTN fournit services mobiles, money mobile et données à plus de 280 millions d'abonnés. Le groupe est un acteur clé de la digitalisation africaine.",
    
    "SBK": "Standard Bank Group est la plus grande banque africaine par actifs. Présente dans 20 pays africains, la banque sud-africaine offre services bancaires, assurances et gestion d'actifs. Standard Bank accompagne le développement économique du continent.",
    
    "AGL": "Anglo American plc est un géant minier diversifié extrayant diamants (De Beers), platine, cuivre et minerai de fer. Le groupe britannique coté à Londres et Johannesburg est un acteur majeur de l'industrie minière mondiale.",
    
    "BTI": "British American Tobacco est l'un des plus grands fabricants de tabac au monde avec des marques comme Lucky Strike, Dunhill et Pall Mall. Le groupe investit dans les produits à risque réduit (vapotage, tabac chauffé) pour sa transformation.",
    
    "SOL": "Sasol Limited est un groupe pétrochimique et énergétique sud-africain, pionnier de la technologie coal-to-liquids. Sasol produit carburants, produits chimiques et gaz. L'entreprise investit dans l'hydrogène vert et les énergies renouvelables.",
    
    # ============================================
    # ETFs
    # ============================================
    "SPY": "SPDR S&P 500 ETF Trust est le plus grand ETF au monde, répliquant l'indice S&P 500. Lancé en 1993, SPY offre une exposition aux 500 plus grandes entreprises américaines. C'est l'instrument le plus liquide pour investir dans les actions US.",
    
    "QQQ": "Invesco QQQ Trust réplique l'indice Nasdaq-100, offrant une exposition aux 100 plus grandes entreprises non-financières du Nasdaq. Dominé par les géants technologiques (Apple, Microsoft, Nvidia), QQQ est l'ETF de référence pour la tech US.",
    
    "VOO": "Vanguard S&P 500 ETF réplique l'indice S&P 500 avec des frais parmi les plus bas du marché (0.03%). Géré par Vanguard, pionnier de la gestion passive, VOO est l'un des ETF les plus populaires auprès des investisseurs long terme.",
    
    "VTI": "Vanguard Total Stock Market ETF offre une exposition à l'ensemble du marché actions américain, incluant petites, moyennes et grandes capitalisations. VTI détient plus de 4 000 actions, offrant une diversification maximale.",
    
    "IWM": "iShares Russell 2000 ETF réplique l'indice des petites capitalisations américaines. IWM offre une exposition à 2 000 small caps US, souvent considérées comme un indicateur avancé de l'économie américaine.",
    
    "HYG": "iShares iBoxx $ High Yield Corporate Bond ETF offre une exposition aux obligations d'entreprises à haut rendement (high yield). HYG permet d'investir dans des obligations corporate offrant des rendements supérieurs en échange d'un risque de crédit plus élevé.",
    
    "LQD": "iShares iBoxx $ Investment Grade Corporate Bond ETF offre une exposition aux obligations d'entreprises de qualité investment grade. LQD est l'ETF de référence pour les obligations corporate américaines de haute qualité.",
    
    "TLT": "iShares 20+ Year Treasury Bond ETF offre une exposition aux bons du Trésor américain à long terme (20+ ans). TLT est très sensible aux variations des taux d'intérêt et sert souvent de couverture en période d'aversion au risque.",
    
    "GLD": "SPDR Gold Shares est le plus grand ETF adossé à l'or physique. GLD permet d'investir dans l'or sans détenir le métal physique. L'or est traditionnellement considéré comme une valeur refuge en période d'incertitude.",
}

# Sectors mapping
COMPANY_SECTORS = {
    # US Tech
    "AAPL": ("Technologie", "Électronique grand public"),
    "MSFT": ("Technologie", "Logiciels"),
    "GOOGL": ("Technologie", "Internet"),
    "AMZN": ("Technologie", "E-commerce / Cloud"),
    "META": ("Technologie", "Réseaux sociaux"),
    "NVDA": ("Technologie", "Semi-conducteurs"),
    "TSLA": ("Automobile", "Véhicules électriques"),
    # US Finance
    "JPM": ("Finance", "Banque"),
    "V": ("Finance", "Paiements"),
    "MA": ("Finance", "Paiements"),
    # France
    "MC": ("Consommation", "Luxe"),
    "OR": ("Consommation", "Cosmétiques"),
    "SAN": ("Santé", "Pharmaceutique"),
    "TTE": ("Énergie", "Pétrole & Gaz"),
    "BNP": ("Finance", "Banque"),
    "AI": ("Industrie", "Gaz industriels"),
    "CAP": ("Technologie", "Services IT"),
    "ORA": ("Télécommunications", "Opérateur"),
    # Germany
    "SAP": ("Technologie", "Logiciels"),
    "SIE": ("Industrie", "Conglomérat"),
    "ALV": ("Finance", "Assurance"),
    "BMW": ("Automobile", "Constructeur premium"),
    "DTE": ("Télécommunications", "Opérateur"),
    "VOW3": ("Automobile", "Constructeur"),
    "ADS": ("Consommation", "Équipements sportifs"),
    # UK
    "SHEL": ("Énergie", "Pétrole & Gaz"),
    "AZN": ("Santé", "Pharmaceutique"),
    "HSBA": ("Finance", "Banque"),
    "ULVR": ("Consommation", "Biens de consommation"),
    "BP": ("Énergie", "Pétrole & Gaz"),
    "GSK": ("Santé", "Pharmaceutique"),
    "RIO": ("Matériaux", "Mines"),
    "BARC": ("Finance", "Banque"),
    "VOD": ("Télécommunications", "Opérateur"),
    # South Africa
    "NPN": ("Technologie", "Internet / Médias"),
    "MTN": ("Télécommunications", "Opérateur"),
    "SBK": ("Finance", "Banque"),
    "AGL": ("Matériaux", "Mines"),
    "BTI": ("Consommation", "Tabac"),
    "SOL": ("Énergie", "Pétrochimie"),
    # ETFs
    "SPY": ("ETF", "Actions US Large Cap"),
    "QQQ": ("ETF", "Actions US Tech"),
    "VOO": ("ETF", "Actions US Large Cap"),
    "VTI": ("ETF", "Actions US Total Market"),
    "IWM": ("ETF", "Actions US Small Cap"),
    "HYG": ("ETF", "Obligations High Yield"),
    "LQD": ("ETF", "Obligations Investment Grade"),
    "TLT": ("ETF", "Obligations Trésor Long Terme"),
    "GLD": ("ETF", "Or"),
}


def get_company_description(ticker: str) -> str:
    """Get company description for a ticker."""
    ticker_clean = ticker.upper().replace("_US", "").replace("_PA", "").replace("_XETRA", "").replace("_LSE", "").replace("_JSE", "")
    return COMPANY_DESCRIPTIONS.get(ticker_clean, "")


def get_company_sector(ticker: str) -> tuple:
    """Get company sector and industry."""
    ticker_clean = ticker.upper().replace("_US", "").replace("_PA", "").replace("_XETRA", "").replace("_LSE", "").replace("_JSE", "")
    return COMPANY_SECTORS.get(ticker_clean, ("", ""))
