# 🧭 Guia de Engenharia Xiaomi Vela OS: Xiaomi Smart Band 10 & 9
> Arquitetura de Hardware, RTOS Apache NuttX, QuickApp Runtime, Limitações e Boas Práticas

Este documento reúne todo o conhecimento técnico acumulado sobre a construção de aplicações independentes (**QuickApps**) para a **Xiaomi Smart Band 10** e **Xiaomi Smart Band 9**, equipadas com o sistema operacional **Xiaomi Vela (HyperOS for Wearables)**.

---

## 1. Hardware e Restrições Físicas

Desenvolver para pulseiras inteligentes da classe *Smart Band* exige uma mentalidade de sistemas embarcados de recursos mínimos:

| Subsistema | Especificação Técnica | Impacto no Software |
| :--- | :--- | :--- |
| **SoC / MCU** | Microcontrolador Dual-Core Low-Power (ARM Cortex-M33 / RISC-V) | Sem MMU tradicional. Computação síncrona pesada congela a interface e aciona o Watchdog timer do RTOS. |
| **Memória SRAM** | ~8 MB a 16 MB totais (compartilhados com todo o sistema) | **Heap de aplicação ultralimitado** (~1 MB a 3 MB por app). Vazamentos de memória derrubam a aplicação silenciosamente. |
| **Armazenamento Flash** | 128 MB a 256 MB NOR/NAND Flash | Pacotes `.rpk` devem ter preferencialmente menos de 2–3 MB. Assets devem ser desduplicados. |
| **Display** | AMOLED 1.62"–1.74", 60 Hz, ~326 PPI | Preto puro (`#000000`) desliga pixels (0 mA). Fundos brancos consom até 5x mais energia. |
| **Resolução Virtual** | Matriz lógica `192 × 490 px` (`designWidth: 192`) | O motor mapeia coordenadas lógicas (`192`) para a densidade física do painel. |
| **Bateria** | 233 mAh a 250 mAh (14 a 21 dias nominais) | Loops em JS ou sensores ligados continuamente esgotam a bateria em poucas horas. |
| **I/O & Tátil** | Touchscreen capacitivo; motor tátil (LRA/ERM) | **Sem botões físicos.** Toda a navegação e saída de páginas depende de gestos (swipe) ou cliques na tela. |
| **Conectividade** | Bluetooth Low Energy 5.4 (BLE) | **Sem Wi-Fi nativo no pulso.** Requisições de rede (`@system.fetch`) dependem da ponte BLE com o smartphone. |

---

## 2. Arquitetura de Software: Xiaomi Vela OS & QuickApp

### 2.1 O Núcleo do Sistema
* **Base NuttX RTOS:** O Xiaomi Vela é construído sobre o **Apache NuttX RTOS**, com modelo de memória plana e escalonador em tempo real estrito.
* **Prioridade de Threads:** Interrupções de sensores e rádio Bluetooth têm prioridade sobre a máquina virtual de aplicações.

### 2.2 O Runtime QuickApp
* **Motor JavaScript:** Variante ultraleve do **JerryScript** ou **QuickJS**.
* **Zero Web DOM:** Não há suporte para `window`, `document`, seletores de query ou HTML tradicional.
* **Componentes Nativos:** Tags como `<list>`, `<text>`, `<image>`, `<stack>`, `<input>` são abstrações diretas mapeadas para widgets C++ em tempo de compilação.

---

## 3. Armadilhas Críticas (O que NÃO Fazer)

### ⚠️ 1. O Erro do Bytecode JSC (`--enable-jsc`)
* **Problema:** Flags antigas de compilação em bytecode (`--enable-jsc`) fazem a aplicação abrir com uma **tela preta permanente** ou travar imediatamente na Band 10 / Vela 2.0.
* **Regra:** Compile sempre em **JavaScript ES6 padrão** empacotado (`hap build` / `hap release` puros).

### ⚠️ 2. Invalidação de Cache de Ícones na Memória Flash
* **Problema:** Ao atualizar imagens em `/common/icons/` e reenviar o `.rpk`, a pulseira continua exibindo os ícones antigos.
* **Causa:** O Vela cria uma cache persistente na Flash baseada no caminho e nome do arquivo para poupar leituras de disco.
* **Regra:** Sempre **desinstale a versão antiga da pulseira** antes de instalar uma nova compilação, ou incremente a pasta/versão.

### ⚠️ 3. O Faux-Bold da Fonte MiSans
* **Problema:** `font-weight: bold` causa textos borrados, pixelados e com aberrações visuais.
* **Causa:** O firmware embarca apenas o peso regular da fonte MiSans. O motor tenta simular o negrito inflando artificialmente os pixels (raster stroke dilation).
* **Regra:** Use sempre `font-weight: normal;` e diferencie títulos através de `font-size` (`24px`, `28px`, `32px`).

### ⚠️ 4. Ícones sem Transparência
* **Problema:** Ícones com caixas brancas ou cinzentas criam um quadrado que quebra o design nativo da pulseira.
* **Regra:** Utilize sempre **PNG RGBA com 100% de transparência** ou SVGs vetoriais normalizados em **96 × 96 px**.

### ⚠️ 5. Falta de Gestão do Retorno (Sem Botão Físico)
* **Problema:** O usuário navega para uma tela secundária e não consegue voltar.
* **Regra:** Toda página secundária deve implementar `router.back()` via gesto de deslizar ou toque na tela.

### ⚠️ 6. Vazamento de Timers
* **Problema:** `setInterval` esquecido sem `clearInterval` no `onDestroy()` drena memória e causa crash do RTOS.
* **Regra:** Limpe rigorosamente todos os temporizadores no ciclo de vida `onDestroy()`.

---

## 4. Estrutura Padrão de Arquivos

```text
projeto-vela/
├── manifest.json              # Configuração global, permissões, tela e páginas
├── app.ux                     # Ciclo de vida global da aplicação
├── sign/                      # Chaves criptográficas de assinatura
│   ├── certificate.pem
│   └── private.pem
├── package.json               # Dependências do compilador HAP
└── src/
    ├── common/
    │   ├── icons/             # Ícones 96x96 px RGBA
    │   └── logo.png           # Ícone do menu da pulseira (128x128 ou 96x96)
    └── pages/
        ├── index/index.ux     # Tela inicial com lista ou menu
        └── detalhe/detalhe.ux # Tela secundária
```

---

## 5. Como Iniciar e Compilar ("Como Fazer")

1. **Instalar dependências Node:**
   ```bash
   npm install
   ```

2. **Definir a geometria no `manifest.json`:**
   ```json
   "display": {
     "designWidth": 192,
     "backgroundColor": "#000000"
   }
   ```

3. **Compilar para Produção:**
   ```bash
   npm run release
   ```
   *O arquivo executável `.rpk` assinado será gerado na pasta `dist/`.*

4. **Instalar na Pulseira:**
   * Via **Notify for Xiaomi**: *Definições -> Dispositivo -> Aplicativo de terceiros -> Carregar .rpk*.
   * Via **Mi Fitness Modificado**: Menu oculto de depuração (`ThirdAppDebugFragment`).
