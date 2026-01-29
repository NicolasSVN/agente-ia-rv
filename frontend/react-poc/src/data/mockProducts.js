export const mockProducts = [
  {
    id: '1',
    name: 'HGLG11 - CSHG Logística',
    category: 'FII Logística',
    tickers: ['HGLG11', 'BRCO11', 'XPLG11', 'VILG11'],
    status: 'ativo',
    confidence: 95,
    updatedAt: '2026-01-28T14:30:00',
    rate: '0.60% a.a. + Taxa de Performance de 20% sobre CDI',
    onePage: 'O HGLG11 é um fundo imobiliário focado em galpões logísticos de alta qualidade, com portfólio diversificado em localidades estratégicas. Ideal para investidores que buscam exposição ao setor logístico com alta qualidade de ativos e gestão profissional.',
    whatsappScript: 'Olá! Tenho uma oportunidade interessante para você: o HGLG11, um FII de logística com dividend yield atrativo e portfólio premium. Posso explicar mais sobre as vantagens? 📊',
    materials: [
      { name: 'Relatório Gerencial Jan/26', status: 'atualizado' },
      { name: 'Tabela de Taxas', status: 'atualizado' },
      { name: 'One-Page Comercial', status: 'pendente' },
    ],
  },
  {
    id: '2',
    name: 'KNRI11 - Kinea Renda Imobiliária',
    category: 'FII Híbrido',
    tickers: ['KNRI11', 'KNCR11', 'KNHY11'],
    status: 'ativo',
    confidence: 88,
    updatedAt: '2026-01-27T10:15:00',
    rate: '1.00% a.a.',
    onePage: 'O KNRI11 é um fundo híbrido que combina imóveis corporativos e shopping centers. Gestão Kinea com track record comprovado e diversificação setorial. Recomendado para perfis moderados.',
    whatsappScript: 'Boa tarde! O KNRI11 está com um desconto interessante sobre o valor patrimonial. É um fundo híbrido com gestão Kinea, reconhecida no mercado. Quer que eu apresente os números? 📈',
    materials: [
      { name: 'Relatório Gerencial Jan/26', status: 'atualizado' },
      { name: 'Comparativo de Fundos', status: 'atualizado' },
    ],
  },
  {
    id: '3',
    name: 'VISC11 - Vinci Shopping Centers',
    category: 'FII Shopping',
    tickers: ['VISC11', 'XPML11', 'HSML11'],
    status: 'expirando',
    confidence: 72,
    updatedAt: '2026-01-15T09:00:00',
    rate: '0.95% a.a. + Performance de 20% sobre IPCA + 6%',
    onePage: 'O VISC11 investe em shopping centers de alta qualidade com foco em regiões metropolitanas. A gestão Vinci tem expertise no setor de varejo e trabalha ativamente na valorização dos ativos.',
    whatsappScript: 'Olá! Os shoppings estão em recuperação forte e o VISC11 pode ser uma boa oportunidade. O fundo tem gestão ativa e portfólio diversificado. Posso te enviar o material? 🛒',
    materials: [
      { name: 'Relatório Gerencial Dez/25', status: 'expirado' },
      { name: 'Análise Setorial', status: 'pendente' },
    ],
  },
  {
    id: '4',
    name: 'BTLG11 - BTG Logística',
    category: 'FII Logística',
    tickers: ['BTLG11', 'LVBI11'],
    status: 'ativo',
    confidence: 91,
    updatedAt: '2026-01-26T16:45:00',
    rate: '0.75% a.a.',
    onePage: 'BTLG11 é um fundo de logística do BTG Pactual com foco em galpões classe A. Estratégia de reciclagem de portfólio e forte relacionamento com locatários de primeira linha.',
    whatsappScript: 'Oi! O BTLG11 é uma das melhores opções em FIIs de logística. Gestão BTG, imóveis premium e yield consistente. Vamos conversar sobre como encaixar na sua carteira? 🏭',
    materials: [
      { name: 'Relatório Gerencial Jan/26', status: 'atualizado' },
      { name: 'Tabela de Taxas 2026', status: 'atualizado' },
      { name: 'Comparativo Logística', status: 'atualizado' },
    ],
  },
  {
    id: '5',
    name: 'MXRF11 - Maxi Renda',
    category: 'FII Papel',
    tickers: ['MXRF11', 'KNCR11', 'RECR11'],
    status: 'expirado',
    confidence: 45,
    updatedAt: '2025-12-20T11:00:00',
    rate: '1.20% a.a.',
    onePage: 'O MXRF11 é um fundo de recebíveis imobiliários com foco em CRIs indexados ao CDI e IPCA. Boa liquidez e gestão conservadora, indicado para diversificação em renda fixa imobiliária.',
    whatsappScript: '',
    materials: [
      { name: 'Relatório Gerencial Nov/25', status: 'expirado' },
    ],
  },
  {
    id: '6',
    name: 'XPML11 - XP Malls',
    category: 'FII Shopping',
    tickers: ['XPML11', 'VISC11', 'MALL11'],
    status: 'ativo',
    confidence: 85,
    updatedAt: '2026-01-25T08:30:00',
    rate: '0.85% a.a.',
    onePage: 'XPML11 é o maior fundo de shoppings do Brasil por patrimônio líquido. Portfólio diversificado com participação em shoppings premium de São Paulo a Porto Alegre.',
    whatsappScript: 'Bom dia! O XPML11 é uma excelente porta de entrada para o setor de shopping centers. É o maior FII do segmento e tem ótima liquidez. Posso te explicar a tese? 🏬',
    materials: [
      { name: 'Relatório Gerencial Jan/26', status: 'atualizado' },
      { name: 'One-Page Comercial', status: 'atualizado' },
    ],
  },
];

export const categories = [
  { value: 'fii-logistica', label: 'FII Logística' },
  { value: 'fii-shopping', label: 'FII Shopping' },
  { value: 'fii-hibrido', label: 'FII Híbrido' },
  { value: 'fii-papel', label: 'FII Papel' },
];

export const statuses = [
  { value: 'ativo', label: 'Ativo' },
  { value: 'expirando', label: 'Expirando' },
  { value: 'expirado', label: 'Expirado' },
];

export const allTickers = [...new Set(mockProducts.flatMap(p => p.tickers))].sort();
