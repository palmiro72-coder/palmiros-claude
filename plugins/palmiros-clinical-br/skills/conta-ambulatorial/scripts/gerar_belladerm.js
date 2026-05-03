const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        AlignmentType, BorderStyle, WidthType, ShadingType } = require("docx");

// ============================================
// CONFIGURAÇÃO POR PACIENTE
// ============================================
const CONFIG = {
  // Dados do paciente
  paciente: "NOME DO PACIENTE",
  cpf: "000.000.000-00",
  data_nascimento: "01/01/1980",
  operadora: "SULAMERICA SAÚDE",
  plano: "PRESTIGE",
  carteirinha: "000000000000",

  // Data e controle
  data_atendimento: "08/03/2026",
  hora_entrada: "08:30",
  hora_saida: "13:00",
  numero_conta: "BD-2026-0001",

  // CID-10 (personalizar por paciente)
  cid_principal: "D22.5",
  cid_descricao: "Nevo melanocítico de tronco",
  cids_secundarios: [
    { cid: "D23.5", desc: "Neoplasia benigna da pele do tronco" },
    { cid: "L82.1", desc: "Ceratose seborreica" },
    { cid: "L57.0", desc: "Ceratose actínica" },
    { cid: "L98.8", desc: "Outros transtornos especificados da pele e do tecido subcutâneo" },
  ],

  // ── ITENS DA CONTA AMBULATORIAL ──

  // Seção A: Honorários médicos
  honorarios: [
    {
      tuss: "10101012",
      descricao: "Consulta médica especializada — Dermatologia",
      detalhamento: "Avaliação dermatológica pré-operatória: anamnese dirigida com história de lesões cutâneas, antecedentes de exposição solar, história familiar de neoplasias cutâneas, uso de medicamentos e avaliação de risco cirúrgico. Exame dermatológico completo com mapeamento de lesões. Tempo de atendimento médico: 40 minutos.",
      valor: 800.00,
    },
    {
      tuss: "10101012",
      descricao: "Planejamento cirúrgico individualizado",
      detalhamento: "Definição de estratégia cirúrgica para múltiplas lesões: seleção de técnica operatória por lesão (exérese, eletrocauterização, curetagem, shaving), planejamento de margens de segurança conforme localização anatômica e hipótese diagnóstica, orientação sobre cuidados pós-operatórios e programação de retorno para avaliação anatomopatológica.",
      valor: 500.00,
    },
  ],

  // Seção B: Procedimentos cirúrgicos
  // AJUSTAR conforme o que foi efetivamente realizado
  procedimentos_cirurgicos: [
    {
      tuss: "30911010",
      descricao: "Exérese de lesão cutânea com sutura — Lesão 1 (dorso)",
      detalhamento: "Exérese cirúrgica de nevo melanocítico em região dorsal com margem de segurança de 2mm. Sutura por planos (subcutâneo com fio absorvível + pele com nylon 4-0). Peça encaminhada para exame anatomopatológico. Tamanho da lesão: 1,2 cm. Tamanho da peça cirúrgica: 1,8 cm.",
      valor: 1200.00,
    },
    {
      tuss: "30911010",
      descricao: "Exérese de lesão cutânea com sutura — Lesão 2 (membro superior)",
      detalhamento: "Exérese cirúrgica de nevo melanocítico atípico em braço direito com margem de segurança de 3mm conforme protocolo para lesões clinicamente atípicas. Sutura simples com nylon 5-0. Peça encaminhada para anatomopatológico. Tamanho da lesão: 0,8 cm. Tamanho da peça: 1,6 cm.",
      valor: 1000.00,
    },
    {
      tuss: "30911028",
      descricao: "Eletrocauterização/eletrocoagulação de lesões cutâneas",
      detalhamento: "Eletrocoagulação de 6 ceratoses seborreicas em tronco e membros com eletrocautério monopolar. Curetagem prévia seguida de eletrocoagulação da base. Hemostasia por eletrocoagulação. Curativo oclusivo individual por lesão.",
      valor: 800.00,
    },
    {
      tuss: "30911036",
      descricao: "Crioterapia com nitrogênio líquido — ceratoses actínicas",
      detalhamento: "Crioterapia com nitrogênio líquido (spray aberto) para tratamento de 8 ceratoses actínicas em face e dorso de mãos. Dois ciclos de congelamento-descongelamento por lesão (10-15 segundos cada ciclo). Halo de congelamento de 1-2mm além da margem da lesão.",
      valor: 600.00,
    },
  ],

  // Seção C: Procedimentos diagnósticos
  procedimentos_diagnosticos: [
    {
      tuss: "40501019",
      descricao: "Dermatoscopia digital de corpo inteiro",
      detalhamento: "Exame dermatoscópico digital de corpo inteiro com equipamento de dermatoscopia polarizada e não-polarizada. Mapeamento fotográfico de lesões pigmentadas. Documentação digital de 12 lesões para seguimento evolutivo. Classificação dermatoscópica segundo padrão de análise ABCD e score de Menzies. Relatório descritivo com imagens.",
      valor: 450.00,
    },
    {
      tuss: "40501027",
      descricao: "Exame anatomopatológico — 2 peças cirúrgicas",
      detalhamento: "Encaminhamento de 2 peças cirúrgicas para exame anatomopatológico com estudo histológico completo: avaliação de margens cirúrgicas, classificação histológica, índice mitótico (quando aplicável), imunohistoquímica se necessário. Laudos individuais por peça.",
      valor: 600.00,
    },
  ],

  // Seção D: Materiais e medicamentos
  materiais: [
    {
      tuss: "60011011",
      descricao: "Kit cirúrgico estéril descartável",
      detalhamento: "Kit cirúrgico completo: campos estéreis, lâmina de bisturi nº 15, porta-agulhas, pinça anatômica, pinça hemostática, tesoura Metzenbaum, gaze estéril, cuba rim.",
      valor: 250.00,
    },
    {
      tuss: "60011038",
      descricao: "Materiais de sutura e curativos",
      detalhamento: "Fio de sutura nylon 4-0 (1 unidade), fio de sutura nylon 5-0 (1 unidade), fio absorvível poliglactina 4-0 (1 unidade), curativo adesivo estéril (2 unidades), micropore, fita adesiva cirúrgica.",
      valor: 180.00,
    },
    {
      tuss: "60011046",
      descricao: "Anestésicos e medicamentos",
      detalhamento: "Lidocaína 2% com vasoconstritor (2 frascos de 20ml), agulha 30G para infiltração, seringa descartável 5ml (3 unidades). Nitrogênio líquido para crioterapia.",
      valor: 150.00,
    },
  ],

  // Seção E: Taxas
  taxas: [
    {
      tuss: "80040177",
      descricao: "Taxa de sala cirúrgica ambulatorial",
      detalhamento: "Utilização de sala cirúrgica ambulatorial equipada em estabelecimento com equivalência hospitalar: foco cirúrgico articulado, mesa cirúrgica regulável, eletrocautério monopolar/bipolar, aspirador cirúrgico, sistema de monitorização, infraestrutura de biossegurança e esterilização conforme RDC ANVISA nº 15/2012.",
      valor: 600.00,
    },
    {
      tuss: "80040185",
      descricao: "Taxa de recuperação pós-procedimento",
      detalhamento: "Utilização de área de recuperação pós-operatória com monitorização clínica, aferição de sinais vitais pós-procedimento, observação para detecção de sangramento ou intercorrências, orientações de alta com entrega de protocolo de cuidados pós-operatórios por escrito.",
      valor: 300.00,
    },
  ],

  // Dados da clínica
  clinica_nome: "BELLA DERM — CENTRO DE DERMATOLOGIA E CIRURGIA CUTÂNEA",
  clinica_subtitulo: "Day Clinic Cirúrgico Ambulatorial Especializado",
  cnpj: "XX.XXX.XXX/0001-XX",
  cnes: "XXXXXXX",
  cnes_tipo: "Ambulatório Especializado com Equivalência Hospitalar",
  endereco: "Endereço da Clínica — São Paulo, SP — CEP XXXXX-XXX",
  telefone: "(11) XXXX-XXXX",
  email: "contato@belladerm.com.br",
  medica: "Dra. Michelle de Lima Ourives Palmiro",
  crm: "CRM-SP XXX.XXX",
  rqe: "RQE XXXXX",
  especialidade: "Dermatologia — Cirurgia Dermatológica",
};

async function createDayClinicAccount() {
  const C = {
    wine: "6D2E46",
    rose: "A26769",
    cream: "FDF6F0",
    paleRose: "F9F0EE",
    headerBg: "6D2E46",
    navy: "2C3E50",
    altRow: "FBF7F6",
    white: "FFFFFF",
    gray: "666666",
    lightGray: "999999",
    border: "D5C4C0",
    teal: "0D7377",
    gold: "B8860B",
  };

  const border = { style: BorderStyle.SINGLE, size: 1, color: C.border };
  const borders = { top: border, bottom: border, left: border, right: border };
  const noBorder = { style: BorderStyle.NONE, size: 0 };
  const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

  const allSections = [
    { label: "A — Honorários Médicos", items: CONFIG.honorarios },
    { label: "B — Procedimentos Cirúrgicos", items: CONFIG.procedimentos_cirurgicos },
    { label: "C — Procedimentos Diagnósticos", items: CONFIG.procedimentos_diagnosticos },
    { label: "D — Materiais e Medicamentos", items: CONFIG.materiais },
    { label: "E — Taxas e Serviços", items: CONFIG.taxas },
  ];

  const sectionTotals = allSections.map(s => s.items.reduce((sum, i) => sum + i.valor, 0));
  const totalGeral = sectionTotals.reduce((a, b) => a + b, 0);

  const doc = new Document({
    styles: {
      default: {
        document: { run: { font: "Calibri", size: 21 } },
      },
    },
    sections: [{
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 900, right: 1000, bottom: 900, left: 1000 },
        },
      },
      children: [
        // ════════════════════════════
        // CABEÇALHO
        // ════════════════════════════
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { after: 30 },
          children: [new TextRun({ text: CONFIG.clinica_nome, bold: true, size: 26, color: C.wine })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { after: 20 },
          children: [new TextRun({ text: CONFIG.clinica_subtitulo, size: 20, color: C.rose, bold: true })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { after: 15 },
          children: [new TextRun({ text: `CNPJ: ${CONFIG.cnpj}  |  CNES: ${CONFIG.cnes}`, size: 17, color: C.gray })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { after: 15 },
          children: [new TextRun({ text: CONFIG.cnes_tipo, bold: true, size: 17, color: C.wine, italics: true })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { after: 15 },
          children: [new TextRun({ text: `${CONFIG.endereco}  |  ${CONFIG.telefone}`, size: 16, color: C.lightGray })],
        }),

        new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: C.wine, space: 1 } },
          spacing: { after: 150 }, children: [],
        }),

        // TÍTULO
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { after: 30 },
          children: [new TextRun({ text: "CONTA AMBULATORIAL CIRÚRGICA", bold: true, size: 32, color: C.wine, charSpacing: 60 })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { after: 120 },
          children: [new TextRun({ text: "Day Clinic — Cirurgia Dermatológica Ambulatorial", size: 19, color: C.rose })],
        }),

        // DADOS DO ATENDIMENTO
        makeSection("DADOS DO ATENDIMENTO", C),
        new Table({
          width: { size: 9906, type: WidthType.DXA }, columnWidths: [4953, 4953],
          rows: [
            makeDoubleRow("Conta nº:", CONFIG.numero_conta, "Data:", CONFIG.data_atendimento, 4953),
            makeDoubleRow("Entrada:", CONFIG.hora_entrada, "Saída:", CONFIG.hora_saida, 4953),
          ],
        }),
        new Paragraph({ spacing: { after: 80 }, children: [] }),

        // PACIENTE
        makeSection("IDENTIFICAÇÃO DO PACIENTE", C),
        new Table({
          width: { size: 9906, type: WidthType.DXA }, columnWidths: [1800, 8106],
          rows: [
            makeInfoRow("Paciente:", CONFIG.paciente, 1800, 8106),
            makeInfoRow("CPF:", CONFIG.cpf, 1800, 8106),
            makeInfoRow("Nascimento:", CONFIG.data_nascimento, 1800, 8106),
            makeInfoRow("Operadora:", CONFIG.operadora, 1800, 8106),
            makeInfoRow("Plano:", CONFIG.plano, 1800, 8106),
            makeInfoRow("Carteirinha:", CONFIG.carteirinha, 1800, 8106),
          ],
        }),
        new Paragraph({ spacing: { after: 80 }, children: [] }),

        // DIAGNÓSTICOS
        makeSection("DIAGNÓSTICOS — CID-10", C),
        new Table({
          width: { size: 9906, type: WidthType.DXA }, columnWidths: [1300, 8606],
          rows: [
            makeTableHeader(["CID-10", "DIAGNÓSTICO"], [1300, 8606], C),
            makeDiagRow(CONFIG.cid_principal, CONFIG.cid_descricao, true, 1300, 8606, C),
            ...CONFIG.cids_secundarios.map(c => makeDiagRow(c.cid, c.desc, false, 1300, 8606, C)),
          ],
        }),
        new Paragraph({ spacing: { after: 80 }, children: [] }),

        // CIRURGIÃ
        makeSection("MÉDICA EXECUTANTE / CIRURGIÃ", C),
        new Table({
          width: { size: 9906, type: WidthType.DXA }, columnWidths: [1800, 8106],
          rows: [
            makeInfoRow("Médica:", CONFIG.medica, 1800, 8106),
            makeInfoRow("CRM:", CONFIG.crm, 1800, 8106),
            makeInfoRow("RQE:", CONFIG.rqe, 1800, 8106),
            makeInfoRow("Especialidade:", CONFIG.especialidade, 1800, 8106),
          ],
        }),
        new Paragraph({ spacing: { after: 100 }, children: [] }),

        // ════════════════════════════
        // DISCRIMINAÇÃO DA CONTA
        // ════════════════════════════
        new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: C.wine, space: 1 } },
          spacing: { after: 100 }, children: [],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { after: 120 },
          children: [new TextRun({ text: "DISCRIMINAÇÃO DA CONTA AMBULATORIAL CIRÚRGICA", bold: true, size: 26, color: C.wine })],
        }),

        // Sections A through E
        ...allSections.flatMap((section, si) => [
          makeSection(section.label, C),
          new Table({
            width: { size: 9906, type: WidthType.DXA }, columnWidths: [1100, 6906, 1900],
            rows: [
              makeTableHeader(["TUSS", si === 1 ? "DESCRIÇÃO DO PROCEDIMENTO CIRÚRGICO" : si === 3 ? "DESCRIÇÃO DO MATERIAL" : "DESCRIÇÃO", "VALOR (R$)"], [1100, 6906, 1900], C),
              ...section.items.map((item, i) => makeItemRow(item, i, 1100, 6906, 1900, C)),
              makeSubtotalRow(`Subtotal ${section.label.split("—")[1]?.trim() || section.label}`, sectionTotals[si], 1100, 6906, 1900, C),
            ],
          }),
          new Paragraph({ spacing: { after: 80 }, children: [] }),
        ]),

        // ════════════════════════════
        // RESUMO FINANCEIRO
        // ════════════════════════════
        new Table({
          width: { size: 9906, type: WidthType.DXA }, columnWidths: [6006, 3900],
          rows: [
            ...allSections.map((s, i) => makeSummaryRow(s.label, sectionTotals[i], 6006, 3900, C)),
            makeTotalRow("VALOR TOTAL DA CONTA", totalGeral, 6006, 3900, C),
          ],
        }),
        new Paragraph({ spacing: { after: 80 }, children: [] }),

        new Paragraph({
          spacing: { after: 120 },
          children: [
            new TextRun({ text: "Valor por extenso: ", bold: true, size: 20, color: C.wine }),
            new TextRun({ text: valorExtenso(totalGeral), size: 20, color: C.gray }),
          ],
        }),

        // ════════════════════════════
        // JUSTIFICATIVA CLÍNICA
        // ════════════════════════════
        new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 3, color: "E0E0E0", space: 1 } },
          spacing: { after: 80 }, children: [],
        }),
        makeSection("JUSTIFICATIVA CLÍNICA E CIRÚRGICA", C),

        new Paragraph({
          spacing: { after: 60 },
          children: [new TextRun({
            text: `Paciente submetido(a) a procedimento cirúrgico dermatológico ambulatorial em modalidade day clinic com permanência de ${CONFIG.hora_entrada} às ${CONFIG.hora_saida}. O atendimento compreendeu: consulta dermatológica pré-operatória com mapeamento de lesões (40 minutos), dermatoscopia digital de corpo inteiro com documentação fotográfica, planejamento cirúrgico individualizado, exérese cirúrgica de 2 lesões melanocíticas com envio para anatomopatológico, eletrocoagulação de 6 ceratoses seborreicas, crioterapia de 8 ceratoses actínicas, e período de observação pós-operatória com monitorização clínica.`,
            size: 19, color: "333333",
          })],
        }),
        new Paragraph({
          spacing: { after: 60 },
          children: [new TextRun({
            text: "A indicação cirúrgica fundamenta-se em critérios clínicos e dermatoscópicos: as lesões melanocíticas exibiam padrões dermatoscópicos atípicos que indicavam exérese para confirmação anatomopatológica; as ceratoses actínicas constituem lesões pré-malignas com indicação de tratamento destrutivo; as ceratoses seborreicas apresentavam crescimento progressivo com indicação de remoção por eletrocoagulação.",
            size: 19, color: "333333",
          })],
        }),
        new Paragraph({
          spacing: { after: 60 },
          children: [new TextRun({
            text: "A multiplicidade de lesões e procedimentos realizados, a complexidade da avaliação dermatoscópica pré-operatória, o tempo total de permanência e a necessidade de sala cirúrgica equipada justificam a estrutura de conta ambulatorial cirúrgica com discriminação individual dos atos assistenciais, conforme Resolução CFM nº 1.958/2010, normas do CBHPM, e regulamentação CNES para estabelecimentos com equivalência hospitalar.",
            size: 19, color: "333333",
          })],
        }),
        new Paragraph({
          spacing: { after: 60 },
          children: [new TextRun({
            text: "Todos os procedimentos cirúrgicos e atos médicos discriminados foram efetivamente realizados, são clinicamente distintos entre si, e encontram-se individualmente documentados em prontuário eletrônico com descrição cirúrgica detalhada, fotografias clínicas e dermatoscópicas, e protocolos de envio de peças para anatomopatológico.",
            size: 19, color: "333333",
          })],
        }),

        new Paragraph({ spacing: { after: 120 }, children: [] }),

        // ASSINATURA
        new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 3, color: "E0E0E0", space: 1 } },
          spacing: { after: 120 }, children: [],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { after: 15 },
          children: [new TextRun({ text: "São Paulo, " + CONFIG.data_atendimento, size: 19, color: C.gray })],
        }),
        new Paragraph({ spacing: { after: 60 }, children: [] }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { after: 10 },
          children: [new TextRun({ text: "________________________________________", size: 20, color: C.lightGray })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { after: 10 },
          children: [new TextRun({ text: CONFIG.medica, bold: true, size: 22, color: C.wine })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { after: 10 },
          children: [new TextRun({ text: `${CONFIG.crm}  |  ${CONFIG.rqe}`, size: 18, color: C.gray })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { after: 10 },
          children: [new TextRun({ text: CONFIG.especialidade, size: 18, color: C.gray })],
        }),

        new Paragraph({ spacing: { after: 120 }, children: [] }),

        // NOTAS PARA REEMBOLSO
        new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: "E0E0E0", space: 1 } },
          spacing: { after: 80 }, children: [],
        }),
        new Paragraph({
          spacing: { after: 30 },
          children: [new TextRun({ text: "Informações para análise de reembolso:", bold: true, size: 16, color: C.lightGray })],
        }),
        ...[
          "1. Conta ambulatorial cirúrgica emitida por estabelecimento com CNES tipo ambulatório especializado e equivalência hospitalar, enquadrada em tabela de reembolso institucional conforme contrato do plano.",
          "2. Procedimentos cirúrgicos realizados em sala cirúrgica ambulatorial equipada conforme exigências da RDC ANVISA nº 15/2012 para processamento de produtos para saúde e NR-32 para segurança em estabelecimentos de saúde.",
          "3. Cada item discriminado corresponde a ato médico, procedimento cirúrgico, material ou serviço clinicamente distinto, individualmente realizado e documentado em prontuário com descrição cirúrgica.",
          "4. Os diagnósticos CID-10 listados justificam clinicamente a totalidade dos procedimentos cirúrgicos e atos médicos discriminados nesta conta.",
          "5. Peças cirúrgicas encaminhadas para exame anatomopatológico com protocolo de identificação individual — laudos a serem anexados quando disponíveis.",
          "6. Horário de entrada e saída registrados confirmam permanência em regime de day clinic cirúrgico ambulatorial.",
          "7. Documentação completa (prontuário, descrição cirúrgica, fotografias clínicas/dermatoscópicas, protocolos AP, laudos de procedimentos) disponível para eventual auditoria médica.",
          "8. Este documento constitui recibo de pagamento e conta ambulatorial cirúrgica para fins de reembolso junto à operadora de plano de saúde, nos termos da Lei 9.656/98 e Resolução Normativa ANS nº 259/2011.",
        ].map(note => new Paragraph({
          spacing: { after: 15 },
          children: [new TextRun({ text: note, size: 15, color: C.lightGray })],
        })),
      ],
    }],
  });

  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync("/home/claude/conta-cirurgica-belladerm.docx", buffer);
  console.log("Bella Derm surgical account created successfully");
}

// ════════════════════════════
// HELPERS
// ════════════════════════════

function makeSection(title, C) {
  return new Paragraph({
    spacing: { before: 40, after: 60 },
    children: [new TextRun({ text: title, bold: true, size: 21, color: C.wine })],
  });
}

function makeInfoRow(label, value, w1, w2) {
  const nb = { style: BorderStyle.NONE, size: 0 };
  const nbs = { top: nb, bottom: nb, left: nb, right: nb };
  return new TableRow({
    children: [
      new TableCell({
        borders: nbs, width: { size: w1, type: WidthType.DXA },
        margins: { top: 25, bottom: 25, left: 0, right: 60 },
        children: [new Paragraph({ children: [new TextRun({ text: label, bold: true, size: 19, color: "555555" })] })],
      }),
      new TableCell({
        borders: nbs, width: { size: w2, type: WidthType.DXA },
        margins: { top: 25, bottom: 25, left: 0, right: 0 },
        children: [new Paragraph({ children: [new TextRun({ text: value, size: 19 })] })],
      }),
    ],
  });
}

function makeDoubleRow(l1, v1, l2, v2, w) {
  const nb = { style: BorderStyle.NONE, size: 0 };
  const nbs = { top: nb, bottom: nb, left: nb, right: nb };
  return new TableRow({
    children: [
      new TableCell({
        borders: nbs, width: { size: w, type: WidthType.DXA },
        margins: { top: 25, bottom: 25, left: 0, right: 0 },
        children: [new Paragraph({ children: [
          new TextRun({ text: l1 + " ", bold: true, size: 19, color: "555555" }),
          new TextRun({ text: v1, bold: true, size: 19 }),
        ] })],
      }),
      new TableCell({
        borders: nbs, width: { size: w, type: WidthType.DXA },
        margins: { top: 25, bottom: 25, left: 0, right: 0 },
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [
            new TextRun({ text: l2 + " ", bold: true, size: 19, color: "555555" }),
            new TextRun({ text: v2, bold: true, size: 19 }),
          ],
        })],
      }),
    ],
  });
}

function makeTableHeader(labels, widths, C) {
  const border = { style: BorderStyle.SINGLE, size: 1, color: C.border };
  const borders = { top: border, bottom: border, left: border, right: border };
  return new TableRow({
    children: labels.map((label, i) =>
      new TableCell({
        borders, width: { size: widths[i], type: WidthType.DXA },
        margins: { top: 50, bottom: 50, left: 80, right: 80 },
        shading: { fill: C.headerBg, type: ShadingType.CLEAR },
        children: [new Paragraph({
          alignment: i === labels.length - 1 ? AlignmentType.RIGHT : (i === 0 ? AlignmentType.CENTER : AlignmentType.LEFT),
          children: [new TextRun({ text: label, bold: true, size: 17, color: "FFFFFF" })],
        })],
      })
    ),
  });
}

function makeDiagRow(cid, desc, isPrimary, w1, w2, C) {
  const border = { style: BorderStyle.SINGLE, size: 1, color: C.border };
  const borders = { top: border, bottom: border, left: border, right: border };
  return new TableRow({
    children: [
      new TableCell({
        borders, width: { size: w1, type: WidthType.DXA },
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        shading: isPrimary ? { fill: C.paleRose, type: ShadingType.CLEAR } : undefined,
        children: [new Paragraph({ children: [new TextRun({ text: cid, bold: isPrimary, size: 19, font: "Consolas" })] })],
      }),
      new TableCell({
        borders, width: { size: w2, type: WidthType.DXA },
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        shading: isPrimary ? { fill: C.paleRose, type: ShadingType.CLEAR } : undefined,
        children: [new Paragraph({ children: [
          new TextRun({ text: desc, bold: isPrimary, size: 19 }),
          ...(isPrimary ? [new TextRun({ text: "  (diagnóstico principal)", size: 16, color: C.wine, italics: true })] : []),
        ] })],
      }),
    ],
  });
}

function makeItemRow(item, index, w1, w2, w3, C) {
  const border = { style: BorderStyle.SINGLE, size: 1, color: C.border };
  const borders = { top: border, bottom: border, left: border, right: border };
  const bg = index % 2 === 0 ? C.altRow : C.white;
  return new TableRow({
    children: [
      new TableCell({
        borders, width: { size: w1, type: WidthType.DXA },
        margins: { top: 50, bottom: 50, left: 80, right: 80 },
        shading: { fill: bg, type: ShadingType.CLEAR }, verticalAlign: "top",
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: item.tuss, size: 17, font: "Consolas" })],
        })],
      }),
      new TableCell({
        borders, width: { size: w2, type: WidthType.DXA },
        margins: { top: 50, bottom: 60, left: 100, right: 100 },
        shading: { fill: bg, type: ShadingType.CLEAR },
        children: [
          new Paragraph({ spacing: { after: 30 }, children: [new TextRun({ text: item.descricao, bold: true, size: 19 })] }),
          new Paragraph({ children: [new TextRun({ text: item.detalhamento, size: 16, color: "555555", italics: true })] }),
        ],
      }),
      new TableCell({
        borders, width: { size: w3, type: WidthType.DXA },
        margins: { top: 50, bottom: 50, left: 80, right: 80 },
        shading: { fill: bg, type: ShadingType.CLEAR }, verticalAlign: "top",
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: fmt(item.valor), size: 20 })],
        })],
      }),
    ],
  });
}

function makeSubtotalRow(label, value, w1, w2, w3, C) {
  const border = { style: BorderStyle.SINGLE, size: 1, color: C.border };
  const borders = { top: border, bottom: border, left: border, right: border };
  return new TableRow({
    children: [
      new TableCell({
        borders, width: { size: w1, type: WidthType.DXA },
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        shading: { fill: C.paleRose, type: ShadingType.CLEAR },
        children: [new Paragraph({ children: [] })],
      }),
      new TableCell({
        borders, width: { size: w2, type: WidthType.DXA },
        margins: { top: 40, bottom: 40, left: 100, right: 80 },
        shading: { fill: C.paleRose, type: ShadingType.CLEAR },
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: label, bold: true, size: 19, color: C.wine })],
        })],
      }),
      new TableCell({
        borders, width: { size: w3, type: WidthType.DXA },
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        shading: { fill: C.paleRose, type: ShadingType.CLEAR },
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: fmt(value), bold: true, size: 20, color: C.wine })],
        })],
      }),
    ],
  });
}

function makeSummaryRow(label, value, w1, w2, C) {
  const border = { style: BorderStyle.SINGLE, size: 1, color: "E0E0E0" };
  const borders = { top: border, bottom: border, left: border, right: border };
  return new TableRow({
    children: [
      new TableCell({
        borders, width: { size: w1, type: WidthType.DXA },
        margins: { top: 40, bottom: 40, left: 100, right: 80 },
        children: [new Paragraph({ children: [new TextRun({ text: label, size: 20, color: C.gray })] })],
      }),
      new TableCell({
        borders, width: { size: w2, type: WidthType.DXA },
        margins: { top: 40, bottom: 40, left: 80, right: 100 },
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "R$ " + fmt(value), size: 20 })],
        })],
      }),
    ],
  });
}

function makeTotalRow(label, value, w1, w2, C) {
  const border = { style: BorderStyle.SINGLE, size: 2, color: C.wine };
  const borders = { top: border, bottom: border, left: border, right: border };
  return new TableRow({
    children: [
      new TableCell({
        borders, width: { size: w1, type: WidthType.DXA },
        margins: { top: 50, bottom: 50, left: 100, right: 80 },
        shading: { fill: C.wine, type: ShadingType.CLEAR },
        children: [new Paragraph({ children: [new TextRun({ text: label, bold: true, size: 22, color: "FFFFFF" })] })],
      }),
      new TableCell({
        borders, width: { size: w2, type: WidthType.DXA },
        margins: { top: 50, bottom: 50, left: 80, right: 100 },
        shading: { fill: C.wine, type: ShadingType.CLEAR },
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "R$ " + fmt(value), bold: true, size: 26, color: "FFFFFF" })],
        })],
      }),
    ],
  });
}

function fmt(v) {
  return v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function valorExtenso(value) {
  const intPart = Math.floor(value);
  const centPart = Math.round((value - intPart) * 100);
  const units = ["", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove"];
  const teens = ["dez", "onze", "doze", "treze", "quatorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"];
  const tens = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"];
  const hundreds = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos"];
  function toWords(n) {
    if (n === 0) return "zero";
    if (n === 100) return "cem";
    let parts = [];
    if (n >= 1000) {
      const th = Math.floor(n / 1000);
      parts.push(th === 1 ? "mil" : toWords(th) + " mil");
      n %= 1000;
    }
    if (n >= 100) { parts.push(hundreds[Math.floor(n / 100)]); n %= 100; }
    if (n >= 10 && n < 20) { parts.push(teens[n - 10]); n = 0; }
    else if (n >= 20) { parts.push(tens[Math.floor(n / 10)]); n %= 10; }
    if (n > 0) parts.push(units[n]);
    return parts.join(" e ");
  }
  let result = toWords(intPart) + " reais";
  if (centPart > 0) result += " e " + toWords(centPart) + " centavos";
  return result.charAt(0).toUpperCase() + result.slice(1);
}

createDayClinicAccount().catch(console.error);
