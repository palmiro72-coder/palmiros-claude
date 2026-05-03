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
  operadora: "BRADESCO SAÚDE",
  plano: "TOP NACIONAL",
  carteirinha: "000000000000",
  titular: "NOME DO TITULAR (se dependente)",

  // Data e controle
  data_atendimento: "08/03/2026",
  hora_entrada: "09:00",
  hora_saida: "12:30",
  numero_conta: "DAY-2026-0001",

  // CID-10
  cid_principal: "E11.65",
  cid_descricao: "Diabetes mellitus tipo 2 com hiperglicemia",
  cids_secundarios: [
    { cid: "E78.5", desc: "Dislipidemia não especificada" },
    { cid: "E66.01", desc: "Obesidade mórbida devida a excesso de calorias" },
    { cid: "I10", desc: "Hipertensão arterial essencial" },
    { cid: "E03.9", desc: "Hipotireoidismo não especificado" },
    { cid: "G47.3", desc: "Apneia de sono obstrutiva" },
  ],

  // ── ITENS DA CONTA AMBULATORIAL ──
  // Seção 1: Honorários médicos
  honorarios: [
    {
      tuss: "10101012",
      descricao: "Consulta médica especializada — Endocrinologia e Metabologia",
      detalhamento: "Avaliação endocrinológica investigativa de paciente com síndrome metabólica complexa pluricomorbida (5 diagnósticos ativos). Anamnese dirigida com revisão de sistemas endócrino, metabólico, cardiovascular, tireoidiano e gonadal. Exame físico endocrinológico completo. Tempo de atendimento médico direto: 75 minutos.",
      valor: 2200.00,
    },
    {
      tuss: "10101012",
      descricao: "Parecer especializado — Análise integrada de exames complementares",
      detalhamento: "Análise correlativa, interpretação e emissão de parecer integrado sobre 18 exames laboratoriais prévios: perfil glicêmico (glicemia, HbA1c, insulina, HOMA-IR, peptídeo C), perfil lipídico (CT, HDL, LDL, TG, Apo B, Lp(a)), perfil tireoidiano (TSH, T4L, T3, anti-TPO), perfil hepático (TGO, TGP, GGT), perfil renal (creatinina, ureia, microalbuminúria), vitamina D, ferritina, PCR ultrassensível. Correlação fisiopatológica entre achados e definição de conduta baseada em evidência.",
      valor: 800.00,
    },
    {
      tuss: "10101012",
      descricao: "Planejamento terapêutico individualizado multiprofissional",
      detalhamento: "Elaboração de plano terapêutico personalizado com: revisão e ajuste de 4 classes farmacológicas em uso, análise de interações medicamentosas, definição de 8 metas clínicas mensuráveis com prazos, estratificação de risco cardiovascular (Framingham/ASCVD), programação de reavaliação escalonada em 30/60/90 dias, orientação para equipe multiprofissional (nutrição, educação física, psicologia). Documento terapêutico entregue ao paciente.",
      valor: 650.00,
    },
  ],

  // Seção 2: Procedimentos diagnósticos
  procedimentos: [
    {
      tuss: "40808041",
      descricao: "Bioimpedância elétrica tetrapolar segmentar",
      detalhamento: "Avaliação de composição corporal por bioimpedância elétrica multifrequencial segmentar: massa magra, massa gorda, água corporal total, água intra e extracelular, taxa metabólica basal estimada, ângulo de fase. Protocolo padronizado com jejum de 4h e bexiga vazia. Laudo emitido com comparação a valores de referência por idade e sexo.",
      valor: 350.00,
    },
    {
      tuss: "40302180",
      descricao: "Download e interpretação de monitorização contínua de glicose (CGM)",
      detalhamento: "Download de dados de sensor de monitorização contínua de glicose (14 dias), análise de padrão glicêmico: tempo no alvo (70-180 mg/dL), tempo em hipoglicemia (<70 e <54), tempo em hiperglicemia (>180 e >250), variabilidade glicêmica (CV%), GMI estimada, padrões circadianos, identificação de excursões pós-prandiais e hipoglicemias noturnas. Relatório AGP (Ambulatory Glucose Profile) interpretado.",
      valor: 450.00,
    },
    {
      tuss: "40808050",
      descricao: "Calorimetria indireta",
      detalhamento: "Mensuração de taxa metabólica de repouso por calorimetria indireta com analisador de gases. Determinação de gasto energético basal, quociente respiratório (RQ), oxidação de substratos (carboidratos, lipídios, proteínas). Comparação com equações preditivas (Harris-Benedict, Mifflin-St Jeor). Laudo com cálculo de necessidade calórica individualizada para meta terapêutica definida.",
      valor: 400.00,
    },
  ],

  // Seção 3: Taxas e serviços
  taxas: [
    {
      tuss: "80040177",
      descricao: "Taxa de sala — uso de estrutura ambulatorial especializada",
      detalhamento: "Utilização de sala de atendimento ambulatorial equipada em estabelecimento com equivalência hospitalar (CNES tipo ambulatorial especializado): estação clínica completa, equipamentos de aferição (balança de precisão, adipômetro, esfigmomanômetro digital calibrado), sistema informatizado de prontuário eletrônico, infraestrutura de biossegurança conforme RDC ANVISA.",
      valor: 400.00,
    },
    {
      tuss: "20104014",
      descricao: "Avaliação nutricional clínica integrada",
      detalhamento: "Avaliação de estado nutricional: antropometria completa (peso, altura, IMC, circunferências), classificação de risco nutricional (NRS-2002), análise de recordatório alimentar de 72h, identificação de deficiências nutricionais baseada em exames laboratoriais, cálculo de macronutrientes individualizados conforme patologias de base. Orientação nutricional terapêutica integrada ao plano endocrinológico.",
      valor: 350.00,
    },
  ],

  // Dados da clínica
  clinica_nome: "CLÍNICA PALMIROS — CENTRO DE ENDOCRINOLOGIA E METABOLISMO",
  clinica_subtitulo: "Day Clinic Ambulatorial Especializado",
  cnpj: "XX.XXX.XXX/0001-XX",
  cnes: "XXXXXXX",
  cnes_tipo: "Ambulatório Especializado com Equivalência Hospitalar",
  endereco: "Endereço da Clínica — São Paulo, SP — CEP XXXXX-XXX",
  telefone: "(11) XXXX-XXXX",
  email: "contato@clinicapalmiros.com.br",
  medico: "Dr. Lucas do Prado Palmiro",
  crm: "CRM-SP 139.089",
  rqe: "RQE 75.065",
  especialidade: "Endocrinologia e Metabologia",
};

async function createDayClinicAccount() {
  // ── COLORS ──
  const C = {
    navy: "0F2B46",
    blue: "1A5276",
    teal: "0D7377",
    lightBlue: "D6EAF8",
    paleBlue: "EBF5FB",
    headerBg: "1A5276",
    altRow: "F7FAFC",
    white: "FFFFFF",
    gray: "666666",
    lightGray: "999999",
    border: "BDC3C7",
    accent: "E67E22",
  };

  const border = { style: BorderStyle.SINGLE, size: 1, color: C.border };
  const borders = { top: border, bottom: border, left: border, right: border };
  const noBorder = { style: BorderStyle.NONE, size: 0 };
  const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };
  const thinBorder = { style: BorderStyle.SINGLE, size: 1, color: "E0E0E0" };
  const thinBorders = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };
  const cm = { top: 50, bottom: 50, left: 100, right: 100 };

  // Calculate totals
  const allItems = [...CONFIG.honorarios, ...CONFIG.procedimentos, ...CONFIG.taxas];
  const totalHonorarios = CONFIG.honorarios.reduce((s, i) => s + i.valor, 0);
  const totalProcedimentos = CONFIG.procedimentos.reduce((s, i) => s + i.valor, 0);
  const totalTaxas = CONFIG.taxas.reduce((s, i) => s + i.valor, 0);
  const totalGeral = totalHonorarios + totalProcedimentos + totalTaxas;

  // ── BUILD DOCUMENT ──
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

        // ════════════════════════════════════════
        // CABEÇALHO INSTITUCIONAL
        // ════════════════════════════════════════
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 30 },
          children: [
            new TextRun({ text: CONFIG.clinica_nome, bold: true, size: 26, font: "Calibri", color: C.navy }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 20 },
          children: [
            new TextRun({ text: CONFIG.clinica_subtitulo, size: 20, color: C.teal, bold: true }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 15 },
          children: [
            new TextRun({ text: `CNPJ: ${CONFIG.cnpj}  |  CNES: ${CONFIG.cnes}`, size: 17, color: C.gray }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 15 },
          children: [
            new TextRun({ text: CONFIG.cnes_tipo, bold: true, size: 17, color: C.blue, italics: true }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 15 },
          children: [
            new TextRun({ text: `${CONFIG.endereco}  |  ${CONFIG.telefone}`, size: 16, color: C.lightGray }),
          ],
        }),

        // Separador
        new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: C.navy, space: 1 } },
          spacing: { after: 150 },
          children: [],
        }),

        // ════════════════════════════════════════
        // TÍTULO: CONTA AMBULATORIAL
        // ════════════════════════════════════════
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 30 },
          children: [
            new TextRun({ text: "CONTA AMBULATORIAL", bold: true, size: 32, color: C.navy, charSpacing: 80 }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 120 },
          children: [
            new TextRun({ text: "Day Clinic — Atendimento Ambulatorial Especializado", size: 19, color: C.teal }),
          ],
        }),

        // ════════════════════════════════════════
        // DADOS DO ATENDIMENTO
        // ════════════════════════════════════════
        makeSection("DADOS DO ATENDIMENTO", C),

        new Table({
          width: { size: 9906, type: WidthType.DXA },
          columnWidths: [4953, 4953],
          rows: [
            makeDoubleRow("Conta nº:", CONFIG.numero_conta, "Data:", CONFIG.data_atendimento, 4953),
            makeDoubleRow("Entrada:", CONFIG.hora_entrada, "Saída:", CONFIG.hora_saida, 4953),
          ],
        }),

        new Paragraph({ spacing: { after: 80 }, children: [] }),

        // ════════════════════════════════════════
        // DADOS DO PACIENTE
        // ════════════════════════════════════════
        makeSection("IDENTIFICAÇÃO DO PACIENTE", C),

        new Table({
          width: { size: 9906, type: WidthType.DXA },
          columnWidths: [1800, 8106],
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

        // ════════════════════════════════════════
        // DIAGNÓSTICOS
        // ════════════════════════════════════════
        makeSection("DIAGNÓSTICOS — CID-10", C),

        new Table({
          width: { size: 9906, type: WidthType.DXA },
          columnWidths: [1300, 8606],
          rows: [
            makeTableHeader(["CID-10", "DIAGNÓSTICO"], [1300, 8606], C),
            makeDiagRow(CONFIG.cid_principal, CONFIG.cid_descricao, true, 1300, 8606),
            ...CONFIG.cids_secundarios.map(c => makeDiagRow(c.cid, c.desc, false, 1300, 8606)),
          ],
        }),

        new Paragraph({ spacing: { after: 80 }, children: [] }),

        // ════════════════════════════════════════
        // MÉDICO RESPONSÁVEL
        // ════════════════════════════════════════
        makeSection("MÉDICO EXECUTANTE", C),

        new Table({
          width: { size: 9906, type: WidthType.DXA },
          columnWidths: [1800, 8106],
          rows: [
            makeInfoRow("Médico:", CONFIG.medico, 1800, 8106),
            makeInfoRow("CRM:", CONFIG.crm, 1800, 8106),
            makeInfoRow("RQE:", CONFIG.rqe, 1800, 8106),
            makeInfoRow("Especialidade:", CONFIG.especialidade, 1800, 8106),
          ],
        }),

        new Paragraph({ spacing: { after: 100 }, children: [] }),

        // ════════════════════════════════════════
        // DISCRIMINAÇÃO DA CONTA
        // ════════════════════════════════════════
        new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: C.navy, space: 1 } },
          spacing: { after: 100 },
          children: [],
        }),

        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 120 },
          children: [
            new TextRun({ text: "DISCRIMINAÇÃO DA CONTA AMBULATORIAL", bold: true, size: 26, color: C.navy }),
          ],
        }),

        // ── SEÇÃO A: HONORÁRIOS ──
        makeSection("A — HONORÁRIOS MÉDICOS", C),

        new Table({
          width: { size: 9906, type: WidthType.DXA },
          columnWidths: [1100, 6906, 1900],
          rows: [
            makeTableHeader(["TUSS", "DESCRIÇÃO DO ATO MÉDICO", "VALOR (R$)"], [1100, 6906, 1900], C),
            ...CONFIG.honorarios.map((item, i) =>
              makeItemRow(item, i, 1100, 6906, 1900, C)
            ),
            makeSubtotalRow("Subtotal Honorários", totalHonorarios, 1100, 6906, 1900, C),
          ],
        }),

        new Paragraph({ spacing: { after: 80 }, children: [] }),

        // ── SEÇÃO B: PROCEDIMENTOS ──
        makeSection("B — PROCEDIMENTOS DIAGNÓSTICOS", C),

        new Table({
          width: { size: 9906, type: WidthType.DXA },
          columnWidths: [1100, 6906, 1900],
          rows: [
            makeTableHeader(["TUSS", "DESCRIÇÃO DO PROCEDIMENTO", "VALOR (R$)"], [1100, 6906, 1900], C),
            ...CONFIG.procedimentos.map((item, i) =>
              makeItemRow(item, i, 1100, 6906, 1900, C)
            ),
            makeSubtotalRow("Subtotal Procedimentos", totalProcedimentos, 1100, 6906, 1900, C),
          ],
        }),

        new Paragraph({ spacing: { after: 80 }, children: [] }),

        // ── SEÇÃO C: TAXAS ──
        makeSection("C — TAXAS E SERVIÇOS AMBULATORIAIS", C),

        new Table({
          width: { size: 9906, type: WidthType.DXA },
          columnWidths: [1100, 6906, 1900],
          rows: [
            makeTableHeader(["TUSS", "DESCRIÇÃO", "VALOR (R$)"], [1100, 6906, 1900], C),
            ...CONFIG.taxas.map((item, i) =>
              makeItemRow(item, i, 1100, 6906, 1900, C)
            ),
            makeSubtotalRow("Subtotal Taxas", totalTaxas, 1100, 6906, 1900, C),
          ],
        }),

        new Paragraph({ spacing: { after: 100 }, children: [] }),

        // ════════════════════════════════════════
        // RESUMO FINANCEIRO
        // ════════════════════════════════════════
        new Table({
          width: { size: 9906, type: WidthType.DXA },
          columnWidths: [6006, 1900, 2000],
          rows: [
            makeSummaryRow("A — Honorários Médicos", totalHonorarios, 6006, 1900, 2000, C, false),
            makeSummaryRow("B — Procedimentos Diagnósticos", totalProcedimentos, 6006, 1900, 2000, C, false),
            makeSummaryRow("C — Taxas e Serviços", totalTaxas, 6006, 1900, 2000, C, false),
            makeTotalRow("VALOR TOTAL DA CONTA", totalGeral, 6006, 1900, 2000, C),
          ],
        }),

        new Paragraph({ spacing: { after: 80 }, children: [] }),

        // ── VALOR POR EXTENSO ──
        new Paragraph({
          spacing: { after: 120 },
          children: [
            new TextRun({ text: "Valor por extenso: ", bold: true, size: 20, color: C.navy }),
            new TextRun({ text: valorExtenso(totalGeral), size: 20, color: C.gray }),
          ],
        }),

        // ════════════════════════════════════════
        // JUSTIFICATIVA CLÍNICA
        // ════════════════════════════════════════
        new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 3, color: "E0E0E0", space: 1 } },
          spacing: { after: 80 },
          children: [],
        }),

        makeSection("JUSTIFICATIVA CLÍNICA", C),

        new Paragraph({
          spacing: { after: 60 },
          children: [
            new TextRun({
              text: "Paciente portador(a) de síndrome metabólica complexa com 5 diagnósticos endócrino-metabólicos ativos e interrelacionados, demandando avaliação investigativa em modalidade day clinic com duração de " + CONFIG.hora_entrada + " às " + CONFIG.hora_saida + ". O atendimento incluiu consulta médica investigativa aprofundada (75 minutos de tempo médico direto), análise integrada de 18 exames laboratoriais prévios, 3 procedimentos diagnósticos instrumentais (bioimpedância segmentar, download/interpretação CGM 14 dias, calorimetria indireta), avaliação nutricional clínica integrada e elaboração de plano terapêutico individualizado multiprofissional.",
              size: 19, color: "333333",
            }),
          ],
        }),
        new Paragraph({
          spacing: { after: 60 },
          children: [
            new TextRun({
              text: "A complexidade clínica, o número de procedimentos realizados e o tempo total de permanência justificam a estrutura de conta ambulatorial com discriminação individual dos atos assistenciais, conforme Resolução CFM nº 1.958/2010, normas do CBHPM e regulamentação CNES para estabelecimentos com equivalência hospitalar.",
              size: 19, color: "333333",
            }),
          ],
        }),
        new Paragraph({
          spacing: { after: 60 },
          children: [
            new TextRun({
              text: "Todos os procedimentos e atos médicos discriminados foram efetivamente realizados, são clinicamente distintos entre si, e encontram-se individualmente documentados em prontuário eletrônico do paciente, disponível para auditoria.",
              size: 19, color: "333333",
            }),
          ],
        }),

        new Paragraph({ spacing: { after: 120 }, children: [] }),

        // ════════════════════════════════════════
        // ASSINATURA
        // ════════════════════════════════════════
        new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 3, color: "E0E0E0", space: 1 } },
          spacing: { after: 120 },
          children: [],
        }),

        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 15 },
          children: [
            new TextRun({ text: "São Paulo, " + CONFIG.data_atendimento, size: 19, color: C.gray }),
          ],
        }),

        new Paragraph({ spacing: { after: 60 }, children: [] }),

        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 10 },
          children: [
            new TextRun({ text: "________________________________________", size: 20, color: C.lightGray }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 10 },
          children: [
            new TextRun({ text: CONFIG.medico, bold: true, size: 22, color: C.navy }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 10 },
          children: [
            new TextRun({ text: `${CONFIG.crm}  |  ${CONFIG.rqe}`, size: 18, color: C.gray }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 10 },
          children: [
            new TextRun({ text: CONFIG.especialidade, size: 18, color: C.gray }),
          ],
        }),

        new Paragraph({ spacing: { after: 120 }, children: [] }),

        // ════════════════════════════════════════
        // NOTAS PARA REEMBOLSO
        // ════════════════════════════════════════
        new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: "E0E0E0", space: 1 } },
          spacing: { after: 80 },
          children: [],
        }),

        new Paragraph({
          spacing: { after: 30 },
          children: [
            new TextRun({ text: "Informações para análise de reembolso:", bold: true, size: 16, color: C.lightGray }),
          ],
        }),
        ...[
          "1. Conta ambulatorial emitida por estabelecimento com CNES tipo ambulatório especializado e equivalência hospitalar, podendo ser enquadrada em tabela de reembolso institucional conforme contrato do plano.",
          "2. Cada item discriminado corresponde a ato médico ou procedimento clinicamente distinto, individualmente realizado e documentado em prontuário, com código TUSS correspondente.",
          "3. Os diagnósticos CID-10 listados justificam clinicamente a totalidade dos procedimentos e atos médicos discriminados nesta conta.",
          "4. Horário de entrada e saída registrados confirmam permanência em regime de day clinic ambulatorial.",
          "5. Documentação clínica completa (prontuário, laudos de procedimentos, relatório AGP, laudo de composição corporal e laudo de calorimetria) disponível para eventual auditoria médica.",
          "6. Este documento constitui recibo de pagamento e conta ambulatorial para fins de reembolso junto à operadora de plano de saúde, nos termos da Lei 9.656/98 e Resolução Normativa ANS nº 259/2011.",
        ].map(note => new Paragraph({
          spacing: { after: 15 },
          children: [
            new TextRun({ text: note, size: 15, color: C.lightGray }),
          ],
        })),
      ],
    }],
  });

  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync("/home/claude/conta-ambulatorial-palmiros.docx", buffer);
  console.log("Day clinic account created successfully");
}

// ════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════

function makeSection(title, C) {
  return new Paragraph({
    spacing: { before: 40, after: 60 },
    children: [
      new TextRun({ text: title, bold: true, size: 21, color: C.navy }),
    ],
  });
}

function makeInfoRow(label, value, w1, w2) {
  const noBorder = { style: BorderStyle.NONE, size: 0 };
  const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };
  return new TableRow({
    children: [
      new TableCell({
        borders: noBorders, width: { size: w1, type: WidthType.DXA },
        margins: { top: 25, bottom: 25, left: 0, right: 60 },
        children: [new Paragraph({ children: [new TextRun({ text: label, bold: true, size: 19, color: "555555" })] })],
      }),
      new TableCell({
        borders: noBorders, width: { size: w2, type: WidthType.DXA },
        margins: { top: 25, bottom: 25, left: 0, right: 0 },
        children: [new Paragraph({ children: [new TextRun({ text: value, size: 19 })] })],
      }),
    ],
  });
}

function makeDoubleRow(l1, v1, l2, v2, w) {
  const noBorder = { style: BorderStyle.NONE, size: 0 };
  const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };
  return new TableRow({
    children: [
      new TableCell({
        borders: noBorders, width: { size: w, type: WidthType.DXA },
        margins: { top: 25, bottom: 25, left: 0, right: 0 },
        children: [new Paragraph({ children: [
          new TextRun({ text: l1 + " ", bold: true, size: 19, color: "555555" }),
          new TextRun({ text: v1, bold: true, size: 19 }),
        ] })],
      }),
      new TableCell({
        borders: noBorders, width: { size: w, type: WidthType.DXA },
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
          children: [new TextRun({ text: label, bold: true, size: 17, color: C.white })],
        })],
      })
    ),
  });
}

function makeDiagRow(cid, desc, isPrimary, w1, w2) {
  const border = { style: BorderStyle.SINGLE, size: 1, color: "BDC3C7" };
  const borders = { top: border, bottom: border, left: border, right: border };
  return new TableRow({
    children: [
      new TableCell({
        borders, width: { size: w1, type: WidthType.DXA },
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        shading: isPrimary ? { fill: "E8F0FE", type: ShadingType.CLEAR } : undefined,
        children: [new Paragraph({ children: [new TextRun({ text: cid, bold: isPrimary, size: 19, font: "Consolas" })] })],
      }),
      new TableCell({
        borders, width: { size: w2, type: WidthType.DXA },
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        shading: isPrimary ? { fill: "E8F0FE", type: ShadingType.CLEAR } : undefined,
        children: [new Paragraph({ children: [
          new TextRun({ text: desc, bold: isPrimary, size: 19 }),
          ...(isPrimary ? [new TextRun({ text: "  (diagnóstico principal)", size: 16, color: "1A5276", italics: true })] : []),
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
        shading: { fill: bg, type: ShadingType.CLEAR },
        verticalAlign: "top",
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
          new Paragraph({
            spacing: { after: 30 },
            children: [new TextRun({ text: item.descricao, bold: true, size: 19 })],
          }),
          new Paragraph({
            children: [new TextRun({ text: item.detalhamento, size: 16, color: "555555", italics: true })],
          }),
        ],
      }),
      new TableCell({
        borders, width: { size: w3, type: WidthType.DXA },
        margins: { top: 50, bottom: 50, left: 80, right: 80 },
        shading: { fill: bg, type: ShadingType.CLEAR },
        verticalAlign: "top",
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
        shading: { fill: "EBF5FB", type: ShadingType.CLEAR },
        children: [new Paragraph({ children: [] })],
      }),
      new TableCell({
        borders, width: { size: w2, type: WidthType.DXA },
        margins: { top: 40, bottom: 40, left: 100, right: 80 },
        shading: { fill: "EBF5FB", type: ShadingType.CLEAR },
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: label, bold: true, size: 19, color: C.navy })],
        })],
      }),
      new TableCell({
        borders, width: { size: w3, type: WidthType.DXA },
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        shading: { fill: "EBF5FB", type: ShadingType.CLEAR },
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: fmt(value), bold: true, size: 20, color: C.navy })],
        })],
      }),
    ],
  });
}

function makeSummaryRow(label, value, w1, w2, w3, C, isTotal) {
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
        borders, width: { size: w2 + w3, type: WidthType.DXA },
        margins: { top: 40, bottom: 40, left: 80, right: 100 },
        columnSpan: 2,
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "R$ " + fmt(value), size: 20 })],
        })],
      }),
    ],
  });
}

function makeTotalRow(label, value, w1, w2, w3, C) {
  const border = { style: BorderStyle.SINGLE, size: 2, color: C.navy };
  const borders = { top: border, bottom: border, left: border, right: border };
  return new TableRow({
    children: [
      new TableCell({
        borders, width: { size: w1, type: WidthType.DXA },
        margins: { top: 50, bottom: 50, left: 100, right: 80 },
        shading: { fill: C.navy, type: ShadingType.CLEAR },
        children: [new Paragraph({ children: [new TextRun({ text: label, bold: true, size: 22, color: C.white })] })],
      }),
      new TableCell({
        borders, width: { size: w2 + w3, type: WidthType.DXA },
        margins: { top: 50, bottom: 50, left: 80, right: 100 },
        columnSpan: 2,
        shading: { fill: C.navy, type: ShadingType.CLEAR },
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "R$ " + fmt(value), bold: true, size: 26, color: C.white })],
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
