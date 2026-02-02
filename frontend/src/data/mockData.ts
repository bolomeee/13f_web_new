export interface Guru {
  id: string;
  name: string;
  avatar: string;
  aum: string;
}

export interface Holding {
  ticker: string;
  company: string;
  shares: number;
  value: string;
  portfolioPercent: number;
  change?: number;
}

export interface OptionPosition {
  ticker: string;
  company: string;
  contracts: number;
  totalValue: string;
  strikePrice: number;
  expiryDate: string;
}

export interface InstitutionDetail {
  id: string;
  name: string;
  avatar: string;
  aum: string;
  increasedPositions: Holding[];
  decreasedPositions: Holding[];
  callOptions: OptionPosition[];
  putOptions: OptionPosition[];
}

export interface TopPick {
  ticker: string;
  company: string;
  guruCount: number;
  sparklineData: number[];
  changePercent: number;
}

export interface TopIncreaseByPercent {
  ticker: string;
  company: string;
  increasePercent: number;
  institution: string;
}

export interface TopDecreaseByPercent {
  ticker: string;
  company: string;
  decreasePercent: number;
  institution: string;
}

export interface TopByInstitutionCount {
  ticker: string;
  company: string;
  institutionCount: number;
  changePercent: number;
}

export interface Activity {
  id: string;
  guruName: string;
  action: 'buy' | 'sell' | 'increase' | 'decrease';
  ticker: string;
  changePercent: number;
  date: string;
}

export interface MonitoredCompany {
  id: string;
  cik: string;
  name: string;
  addedDate: string;
}

export interface Filing {
  id: string;
  date: string;
  quarter: string;
  holdings: number;
}

export interface CompanyWithFilings {
  id: string;
  name: string;
  filings: Filing[];
}

export const trackedGurus: Guru[] = [
  { id: '1', name: 'Berkshire Hathaway', avatar: 'BH', aum: '$360B' },
  { id: '2', name: 'Fisher Investments', avatar: 'FI', aum: '$197B' },
  { id: '3', name: 'Pershing Square', avatar: 'PS', aum: '$14B' },
  { id: '4', name: 'ARK Investment', avatar: 'ARK', aum: '$7.5B' },
  { id: '5', name: 'Appaloosa Management', avatar: 'AM', aum: '$13B' },
  { id: '6', name: 'Bridgewater Associates', avatar: 'BA', aum: '$124B' },
];

export const buffettHoldings: Holding[] = [
  {
    ticker: 'AAPL',
    company: 'Apple Inc',
    shares: 915560000,
    value: '$174.3B',
    portfolioPercent: 48.4,
  },
  {
    ticker: 'BAC',
    company: 'Bank of America',
    shares: 1032852000,
    value: '$34.2B',
    portfolioPercent: 9.5,
  },
  {
    ticker: 'CVX',
    company: 'Chevron Corp',
    shares: 132416000,
    value: '$19.4B',
    portfolioPercent: 5.4,
  },
  {
    ticker: 'KO',
    company: 'Coca-Cola Co',
    shares: 400000000,
    value: '$24.1B',
    portfolioPercent: 6.7,
  },
  {
    ticker: 'AXP',
    company: 'American Express',
    shares: 151610000,
    value: '$28.7B',
    portfolioPercent: 8.0,
  },
];

export const institutionDetails: Record<string, InstitutionDetail> = {
  '1': {
    id: '1',
    name: 'Berkshire Hathaway',
    avatar: 'BH',
    aum: '$360B',
    increasedPositions: [
      {
        ticker: 'AAPL',
        company: 'Apple Inc',
        shares: 15420000,
        value: '$2.93B',
        portfolioPercent: 0.8,
        change: 12.4,
      },
      {
        ticker: 'BAC',
        company: 'Bank of America',
        shares: 45680000,
        value: '$1.52B',
        portfolioPercent: 0.4,
        change: 6.3,
      },
      {
        ticker: 'CVX',
        company: 'Chevron Corp',
        shares: 8920000,
        value: '$1.31B',
        portfolioPercent: 0.4,
        change: 8.7,
      },
    ],
    decreasedPositions: [
      {
        ticker: 'USB',
        company: 'U.S. Bancorp',
        shares: 12340000,
        value: '$540M',
        portfolioPercent: 0.2,
        change: -15.2,
      },
      {
        ticker: 'VZ',
        company: 'Verizon Communications',
        shares: 8650000,
        value: '$345M',
        portfolioPercent: 0.1,
        change: -22.4,
      },
    ],
    callOptions: [
      {
        ticker: 'KO',
        company: 'Coca-Cola Co',
        contracts: 15000,
        totalValue: '$45.2M',
        strikePrice: 58.5,
        expiryDate: '2026-06-20',
      },
      {
        ticker: 'AXP',
        company: 'American Express',
        contracts: 8500,
        totalValue: '$32.1M',
        strikePrice: 175.0,
        expiryDate: '2026-09-18',
      },
    ],
    putOptions: [
      {
        ticker: 'SPY',
        company: 'S&P 500 ETF',
        contracts: 5000,
        totalValue: '$12.5M',
        strikePrice: 480.0,
        expiryDate: '2026-03-20',
      },
    ],
  },
  '2': {
    id: '2',
    name: 'Fisher Investments',
    avatar: 'FI',
    aum: '$197B',
    increasedPositions: [
      {
        ticker: 'MSFT',
        company: 'Microsoft Corp',
        shares: 22450000,
        value: '$8.94B',
        portfolioPercent: 4.5,
        change: 18.3,
      },
      {
        ticker: 'NVDA',
        company: 'NVIDIA Corp',
        shares: 5680000,
        value: '$4.21B',
        portfolioPercent: 2.1,
        change: 25.7,
      },
    ],
    decreasedPositions: [
      {
        ticker: 'GOOGL',
        company: 'Alphabet Inc',
        shares: 18920000,
        value: '$2.65B',
        portfolioPercent: 1.3,
        change: -15.3,
      },
      {
        ticker: 'META',
        company: 'Meta Platforms',
        shares: 6540000,
        value: '$1.98B',
        portfolioPercent: 1.0,
        change: -9.8,
      },
    ],
    callOptions: [
      {
        ticker: 'TSLA',
        company: 'Tesla Inc',
        contracts: 12000,
        totalValue: '$68.4M',
        strikePrice: 225.0,
        expiryDate: '2026-12-18',
      },
    ],
    putOptions: [
      {
        ticker: 'QQQ',
        company: 'Nasdaq-100 ETF',
        contracts: 8000,
        totalValue: '$24.8M',
        strikePrice: 395.0,
        expiryDate: '2026-06-19',
      },
    ],
  },
  '3': {
    id: '3',
    name: 'Pershing Square',
    avatar: 'PS',
    aum: '$14B',
    increasedPositions: [
      {
        ticker: 'MSFT',
        company: 'Microsoft Corp',
        shares: 3420000,
        value: '$1.36B',
        portfolioPercent: 9.7,
        change: 22.1,
      },
      {
        ticker: 'CMG',
        company: 'Chipotle Mexican Grill',
        shares: 1580000,
        value: '$890M',
        portfolioPercent: 6.4,
        change: 14.5,
      },
    ],
    decreasedPositions: [
      {
        ticker: 'HLT',
        company: 'Hilton Worldwide',
        shares: 2340000,
        value: '$456M',
        portfolioPercent: 3.3,
        change: -8.2,
      },
    ],
    callOptions: [],
    putOptions: [],
  },
  '4': {
    id: '4',
    name: 'ARK Investment',
    avatar: 'ARK',
    aum: '$7.5B',
    increasedPositions: [
      {
        ticker: 'TSLA',
        company: 'Tesla Inc',
        shares: 4680000,
        value: '$1.05B',
        portfolioPercent: 14.0,
        change: 8.7,
      },
      {
        ticker: 'ROKU',
        company: 'Roku Inc',
        shares: 12450000,
        value: '$845M',
        portfolioPercent: 11.3,
        change: 15.2,
      },
    ],
    decreasedPositions: [
      {
        ticker: 'COIN',
        company: 'Coinbase Global',
        shares: 8920000,
        value: '$1.52B',
        portfolioPercent: 20.3,
        change: -30.2,
      },
      {
        ticker: 'HOOD',
        company: 'Robinhood Markets',
        shares: 15680000,
        value: '$387M',
        portfolioPercent: 5.2,
        change: -18.6,
      },
    ],
    callOptions: [
      {
        ticker: 'TSLA',
        company: 'Tesla Inc',
        contracts: 25000,
        totalValue: '$142.5M',
        strikePrice: 250.0,
        expiryDate: '2027-01-15',
      },
      {
        ticker: 'SQ',
        company: 'Block Inc',
        contracts: 18000,
        totalValue: '$52.2M',
        strikePrice: 75.0,
        expiryDate: '2026-08-21',
      },
    ],
    putOptions: [],
  },
  '5': {
    id: '5',
    name: 'Appaloosa Management',
    avatar: 'AM',
    aum: '$13B',
    increasedPositions: [
      {
        ticker: 'NVDA',
        company: 'NVIDIA Corp',
        shares: 2890000,
        value: '$2.14B',
        portfolioPercent: 16.5,
        change: 18.9,
      },
      {
        ticker: 'AMZN',
        company: 'Amazon.com Inc',
        shares: 5420000,
        value: '$1.08B',
        portfolioPercent: 8.3,
        change: 11.2,
      },
    ],
    decreasedPositions: [
      {
        ticker: 'SPY',
        company: 'S&P 500 ETF',
        shares: 1240000,
        value: '$598M',
        portfolioPercent: 4.6,
        change: -5.8,
      },
    ],
    callOptions: [
      {
        ticker: 'AMD',
        company: 'Advanced Micro Devices',
        contracts: 20000,
        totalValue: '$78.4M',
        strikePrice: 145.0,
        expiryDate: '2026-07-17',
      },
    ],
    putOptions: [
      {
        ticker: 'TLT',
        company: 'iShares 20+ Year Treasury',
        contracts: 15000,
        totalValue: '$18.9M',
        strikePrice: 92.0,
        expiryDate: '2026-04-17',
      },
    ],
  },
  '6': {
    id: '6',
    name: 'Bridgewater Associates',
    avatar: 'BA',
    aum: '$124B',
    increasedPositions: [
      {
        ticker: 'VTI',
        company: 'Vanguard Total Stock Market ETF',
        shares: 18920000,
        value: '$4.73B',
        portfolioPercent: 3.8,
        change: 7.4,
      },
      {
        ticker: 'EEM',
        company: 'iShares MSCI Emerging Markets',
        shares: 45680000,
        value: '$2.28B',
        portfolioPercent: 1.8,
        change: 12.3,
      },
    ],
    decreasedPositions: [
      {
        ticker: 'SPY',
        company: 'S&P 500 ETF',
        shares: 8920000,
        value: '$4.30B',
        portfolioPercent: 3.5,
        change: -5.8,
      },
      {
        ticker: 'GLD',
        company: 'SPDR Gold Trust',
        shares: 12340000,
        value: '$2.59B',
        portfolioPercent: 2.1,
        change: -8.4,
      },
    ],
    callOptions: [],
    putOptions: [
      {
        ticker: 'SPY',
        company: 'S&P 500 ETF',
        contracts: 50000,
        totalValue: '$125.0M',
        strikePrice: 475.0,
        expiryDate: '2026-06-19',
      },
      {
        ticker: 'IWM',
        company: 'iShares Russell 2000',
        contracts: 30000,
        totalValue: '$45.6M',
        strikePrice: 195.0,
        expiryDate: '2026-09-18',
      },
    ],
  },
};

export const topIncreasesByPercent: TopIncreaseByPercent[] = [
  { ticker: 'NVDA', company: 'NVIDIA Corp', increasePercent: 25.7, institution: 'Fisher Investments' },
  { ticker: 'MSFT', company: 'Microsoft Corp', increasePercent: 22.1, institution: 'Pershing Square' },
  { ticker: 'NVDA', company: 'NVIDIA Corp', increasePercent: 18.9, institution: 'Appaloosa Management' },
  { ticker: 'MSFT', company: 'Microsoft Corp', increasePercent: 18.3, institution: 'Fisher Investments' },
  { ticker: 'ROKU', company: 'Roku Inc', increasePercent: 15.2, institution: 'ARK Investment' },
  { ticker: 'CMG', company: 'Chipotle Mexican Grill', increasePercent: 14.5, institution: 'Pershing Square' },
  { ticker: 'AAPL', company: 'Apple Inc', increasePercent: 12.4, institution: 'Berkshire Hathaway' },
  { ticker: 'EEM', company: 'iShares MSCI Emerging Markets', increasePercent: 12.3, institution: 'Bridgewater Associates' },
  { ticker: 'AMZN', company: 'Amazon.com Inc', increasePercent: 11.2, institution: 'Appaloosa Management' },
  { ticker: 'TSLA', company: 'Tesla Inc', increasePercent: 8.7, institution: 'ARK Investment' },
  { ticker: 'CVX', company: 'Chevron Corp', increasePercent: 8.7, institution: 'Berkshire Hathaway' },
  { ticker: 'VTI', company: 'Vanguard Total Stock Market ETF', increasePercent: 7.4, institution: 'Bridgewater Associates' },
  { ticker: 'BAC', company: 'Bank of America', increasePercent: 6.3, institution: 'Berkshire Hathaway' },
  { ticker: 'SQ', company: 'Block Inc', increasePercent: 5.8, institution: 'ARK Investment' },
  { ticker: 'AMD', company: 'Advanced Micro Devices', increasePercent: 5.4, institution: 'Appaloosa Management' },
  { ticker: 'COIN', company: 'Coinbase Global', increasePercent: 4.9, institution: 'ARK Investment' },
  { ticker: 'SHOP', company: 'Shopify Inc', increasePercent: 4.2, institution: 'Fisher Investments' },
  { ticker: 'UBER', company: 'Uber Technologies', increasePercent: 3.8, institution: 'Pershing Square' },
  { ticker: 'NFLX', company: 'Netflix Inc', increasePercent: 3.5, institution: 'Appaloosa Management' },
  { ticker: 'DIS', company: 'Walt Disney Co', increasePercent: 3.1, institution: 'Bridgewater Associates' },
];

export const topDecreasesByPercent: TopDecreaseByPercent[] = [
  { ticker: 'TDOC', company: 'Teladoc Health', decreasePercent: -42.6, institution: 'ARK Investment' },
  { ticker: 'SOFI', company: 'SoFi Technologies', decreasePercent: -38.7, institution: 'Appaloosa Management' },
  { ticker: 'SNAP', company: 'Snap Inc', decreasePercent: -35.1, institution: 'Bridgewater Associates' },
  { ticker: 'ROKU', company: 'Roku Inc', decreasePercent: -33.5, institution: 'ARK Investment' },
  { ticker: 'RBLX', company: 'Roblox Corp', decreasePercent: -31.2, institution: 'ARK Investment' },
  { ticker: 'COIN', company: 'Coinbase Global', decreasePercent: -30.2, institution: 'ARK Investment' },
  { ticker: 'LYFT', company: 'Lyft Inc', decreasePercent: -28.4, institution: 'Fisher Investments' },
  { ticker: 'ZM', company: 'Zoom Video', decreasePercent: -27.9, institution: 'Bridgewater Associates' },
  { ticker: 'ARKK', company: 'ARK Innovation ETF', decreasePercent: -25.6, institution: 'Pershing Square' },
  { ticker: 'DKNG', company: 'DraftKings Inc', decreasePercent: -24.1, institution: 'Appaloosa Management' },
  { ticker: 'SQ', company: 'Block Inc', decreasePercent: -22.7, institution: 'Fisher Investments' },
  { ticker: 'PLTR', company: 'Palantir Technologies', decreasePercent: -20.8, institution: 'ARK Investment' },
  { ticker: 'PYPL', company: 'PayPal Holdings', decreasePercent: -19.3, institution: 'Berkshire Hathaway' },
  { ticker: 'TSLA', company: 'Tesla Inc', decreasePercent: -18.4, institution: 'Bridgewater Associates' },
  { ticker: 'PINS', company: 'Pinterest Inc', decreasePercent: -16.8, institution: 'Fisher Investments' },
  { ticker: 'GOOGL', company: 'Alphabet Inc', decreasePercent: -15.3, institution: 'Pershing Square' },
  { ticker: 'SHOP', company: 'Shopify Inc', decreasePercent: -14.2, institution: 'Appaloosa Management' },
  { ticker: 'META', company: 'Meta Platforms', decreasePercent: -12.8, institution: 'Berkshire Hathaway' },
  { ticker: 'UBER', company: 'Uber Technologies', decreasePercent: -11.5, institution: 'Fisher Investments' },
  { ticker: 'SPY', company: 'S&P 500 ETF', decreasePercent: -8.9, institution: 'Bridgewater Associates' },
];

export const topIncreasesByInstitutions: TopByInstitutionCount[] = [
  { ticker: 'MSFT', company: 'Microsoft Corp', institutionCount: 142, changePercent: 18.2 },
  { ticker: 'NVDA', company: 'NVIDIA Corp', institutionCount: 115, changePercent: 22.3 },
  { ticker: 'AAPL', company: 'Apple Inc', institutionCount: 98, changePercent: 8.7 },
  { ticker: 'AMZN', company: 'Amazon.com Inc', institutionCount: 87, changePercent: 11.5 },
  { ticker: 'GOOGL', company: 'Alphabet Inc', institutionCount: 76, changePercent: 9.1 },
  { ticker: 'TSLA', company: 'Tesla Inc', institutionCount: 68, changePercent: 15.3 },
  { ticker: 'META', company: 'Meta Platforms', institutionCount: 62, changePercent: 12.8 },
  { ticker: 'AMD', company: 'Advanced Micro Devices', institutionCount: 58, changePercent: 14.2 },
  { ticker: 'NFLX', company: 'Netflix Inc', institutionCount: 54, changePercent: 10.5 },
  { ticker: 'V', company: 'Visa Inc', institutionCount: 51, changePercent: 7.9 },
  { ticker: 'JPM', company: 'JPMorgan Chase', institutionCount: 48, changePercent: 6.4 },
  { ticker: 'MA', company: 'Mastercard Inc', institutionCount: 45, changePercent: 8.1 },
  { ticker: 'UNH', company: 'UnitedHealth Group', institutionCount: 43, changePercent: 5.7 },
  { ticker: 'LLY', company: 'Eli Lilly', institutionCount: 40, changePercent: 13.6 },
  { ticker: 'AVGO', company: 'Broadcom Inc', institutionCount: 38, changePercent: 11.8 },
  { ticker: 'WMT', company: 'Walmart Inc', institutionCount: 36, changePercent: 4.9 },
  { ticker: 'JNJ', company: 'Johnson & Johnson', institutionCount: 34, changePercent: 3.2 },
  { ticker: 'XOM', company: 'Exxon Mobil', institutionCount: 32, changePercent: 6.8 },
  { ticker: 'PG', company: 'Procter & Gamble', institutionCount: 30, changePercent: 4.1 },
  { ticker: 'HD', company: 'Home Depot', institutionCount: 28, changePercent: 5.3 },
];

export const topDecreasesByInstitutions: TopByInstitutionCount[] = [
  { ticker: 'COIN', company: 'Coinbase Global', institutionCount: 68, changePercent: -30.2 },
  { ticker: 'META', company: 'Meta Platforms', institutionCount: 52, changePercent: -12.8 },
  { ticker: 'TSLA', company: 'Tesla Inc', institutionCount: 45, changePercent: -18.4 },
  { ticker: 'GOOGL', company: 'Alphabet Inc', institutionCount: 38, changePercent: -15.3 },
  { ticker: 'SPY', company: 'S&P 500 ETF', institutionCount: 32, changePercent: -8.9 },
  { ticker: 'ARKK', company: 'ARK Innovation ETF', institutionCount: 30, changePercent: -25.6 },
  { ticker: 'SHOP', company: 'Shopify Inc', institutionCount: 28, changePercent: -14.2 },
  { ticker: 'SQ', company: 'Block Inc', institutionCount: 26, changePercent: -22.7 },
  { ticker: 'SNAP', company: 'Snap Inc', institutionCount: 24, changePercent: -35.1 },
  { ticker: 'PYPL', company: 'PayPal Holdings', institutionCount: 22, changePercent: -19.3 },
  { ticker: 'PINS', company: 'Pinterest Inc', institutionCount: 20, changePercent: -16.8 },
  { ticker: 'UBER', company: 'Uber Technologies', institutionCount: 19, changePercent: -11.5 },
  { ticker: 'LYFT', company: 'Lyft Inc', institutionCount: 18, changePercent: -28.4 },
  { ticker: 'RBLX', company: 'Roblox Corp', institutionCount: 17, changePercent: -31.2 },
  { ticker: 'TDOC', company: 'Teladoc Health', institutionCount: 16, changePercent: -42.6 },
  { ticker: 'ZM', company: 'Zoom Video', institutionCount: 15, changePercent: -27.9 },
  { ticker: 'ROKU', company: 'Roku Inc', institutionCount: 14, changePercent: -33.5 },
  { ticker: 'DKNG', company: 'DraftKings Inc', institutionCount: 13, changePercent: -24.1 },
  { ticker: 'PLTR', company: 'Palantir Technologies', institutionCount: 12, changePercent: -20.8 },
  { ticker: 'SOFI', company: 'SoFi Technologies', institutionCount: 11, changePercent: -38.7 },
];

export const topPicks: TopPick[] = [
  {
    ticker: 'MSFT',
    company: 'Microsoft Corp',
    guruCount: 142,
    sparklineData: [100, 105, 103, 108, 112, 115, 118],
    changePercent: 18.2,
  },
  {
    ticker: 'GOOGL',
    company: 'Alphabet Inc',
    guruCount: 128,
    sparklineData: [100, 98, 102, 104, 107, 105, 109],
    changePercent: 9.1,
  },
  {
    ticker: 'NVDA',
    company: 'NVIDIA Corp',
    guruCount: 115,
    sparklineData: [100, 110, 115, 112, 120, 125, 130],
    changePercent: 30.4,
  },
  {
    ticker: 'AAPL',
    company: 'Apple Inc',
    guruCount: 156,
    sparklineData: [100, 101, 99, 102, 104, 106, 105],
    changePercent: 5.2,
  },
  {
    ticker: 'META',
    company: 'Meta Platforms',
    guruCount: 98,
    sparklineData: [100, 95, 98, 103, 108, 110, 114],
    changePercent: 14.3,
  },
  {
    ticker: 'AMZN',
    company: 'Amazon.com Inc',
    guruCount: 134,
    sparklineData: [100, 102, 104, 103, 106, 108, 111],
    changePercent: 11.5,
  },
];

export const recentActivities: Activity[] = [
  {
    id: '1',
    guruName: 'Berkshire Hathaway',
    action: 'buy',
    ticker: 'AAPL',
    changePercent: 12.4,
    date: '2026-01-28',
  },
  {
    id: '2',
    guruName: 'ARK Investment',
    action: 'increase',
    ticker: 'TSLA',
    changePercent: 8.7,
    date: '2026-01-27',
  },
  {
    id: '3',
    guruName: 'Fisher Investments',
    action: 'sell',
    ticker: 'GOOGL',
    changePercent: -15.3,
    date: '2026-01-27',
  },
  {
    id: '4',
    guruName: 'Pershing Square',
    action: 'buy',
    ticker: 'MSFT',
    changePercent: 22.1,
    date: '2026-01-26',
  },
  {
    id: '5',
    guruName: 'Bridgewater Associates',
    action: 'decrease',
    ticker: 'SPY',
    changePercent: -5.8,
    date: '2026-01-25',
  },
  {
    id: '6',
    guruName: 'Appaloosa Management',
    action: 'increase',
    ticker: 'NVDA',
    changePercent: 18.9,
    date: '2026-01-25',
  },
  {
    id: '7',
    guruName: 'ARK Investment',
    action: 'sell',
    ticker: 'COIN',
    changePercent: -30.2,
    date: '2026-01-24',
  },
  {
    id: '8',
    guruName: 'Berkshire Hathaway',
    action: 'increase',
    ticker: 'BAC',
    changePercent: 6.3,
    date: '2026-01-23',
  },
];

export const monitoredCompanies: MonitoredCompany[] = [
  { id: '1', cik: '0000789019', name: 'Microsoft Corporation', addedDate: '2024-03-15' },
  { id: '2', cik: '0001652044', name: 'Alphabet Inc.', addedDate: '2024-04-22' },
  { id: '3', cik: '0001045810', name: 'NVIDIA Corporation', addedDate: '2024-05-10' },
  { id: '4', cik: '0000320193', name: 'Apple Inc.', addedDate: '2024-02-08' },
  { id: '5', cik: '0001326801', name: 'Meta Platforms, Inc.', addedDate: '2024-06-30' },
];

export const companiesWithFilings: CompanyWithFilings[] = [
  {
    id: '1',
    name: 'Microsoft Corporation',
    filings: [
      { id: '1-1', date: '2025-11-14', quarter: 'Q3 2025', holdings: 3421 },
      { id: '1-2', date: '2025-08-14', quarter: 'Q2 2025', holdings: 3298 },
      { id: '1-3', date: '2025-05-15', quarter: 'Q1 2025', holdings: 3156 },
      { id: '1-4', date: '2025-02-14', quarter: 'Q4 2024', holdings: 3087 },
    ],
  },
  {
    id: '2',
    name: 'Alphabet Inc.',
    filings: [
      { id: '2-1', date: '2025-11-14', quarter: 'Q3 2025', holdings: 2867 },
      { id: '2-2', date: '2025-08-14', quarter: 'Q2 2025', holdings: 2754 },
      { id: '2-3', date: '2025-05-15', quarter: 'Q1 2025', holdings: 2689 },
    ],
  },
  {
    id: '3',
    name: 'NVIDIA Corporation',
    filings: [
      { id: '3-1', date: '2025-11-14', quarter: 'Q3 2025', holdings: 4521 },
      { id: '3-2', date: '2025-08-14', quarter: 'Q2 2025', holdings: 4123 },
    ],
  },
];