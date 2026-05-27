"""Segunda passagem de tradução ES→PT-BR em main.py."""

TEXT_MAP2 = [
    # ── Saúde ─────────────────────────────────────────────────────────────
    ('"Completá los datos de la atención que recibió el animal."',
     '"Preencha os dados do atendimento que o animal recebeu."'),
    ('"¿A qué animal?"',                '"Qual animal?"'),
    ('"Tipo de atención"',              '"Tipo de atendimento"'),
    ('"¿Qué tipo de intervención fue?"','"Que tipo de intervenção foi?"'),
    ('"Costo en pesos ($)"',            '"Custo (R$)"'),
    ('"Cuánto costó la atención. Podés dejarlo en 0 si no sabés."',
     '"Quanto custou o atendimento. Pode deixar 0 se não souber."'),
    ('"Anotá los detalles más importantes de la atención."',
     '"Anote os detalhes mais importantes do atendimento."'),
    ('"Primero elegí el animal que fue atendido."',
     '"Primeiro escolha o animal que foi atendido."'),
    # ── Leite ─────────────────────────────────────────────────────────────
    ('"Buscá el animal, indicá cuántos litros produjo y guardá."',
     '"Busque o animal, informe quantos litros produziu e salve."'),
    ('"Paso 1 — Buscá el animal"',
     '"Passo 1 — Busque o animal"'),
    ('"Escribí aquí el nombre del animal…"',
     '"Digite aqui o nome do animal…"'),
    ('"Paso 2 — Ingresá los litros y guardá"',
     '"Passo 2 — Informe os litros e salve"'),
    ('"¿Cuántos litros produjo?"',
     '"Quantos litros produziu?"'),
    ('"Podés usar decimales. Ej: 12.5"',
     '"Pode usar decimais. Ex: 12.5"'),
    ('"Primero buscá y seleccioná el animal en el paso 1."',
     '"Primeiro busque e selecione o animal no passo 1."'),
    # ── Dietas ────────────────────────────────────────────────────────────
    ('"Cuánto come por día cada grupo de animales y qué ingredientes lleva su ración."',
     '"Quanto come por dia cada grupo de animais e quais ingredientes compõem a ração."'),
    ('"Pasá el mouse sobre cada barra de color para ver qué ingrediente representa."',
     '"Passe o mouse sobre cada barra de cor para ver qual ingrediente ela representa."'),
    # ── Estoque ───────────────────────────────────────────────────────────
    ('"Controlá el stock de alimentos y productos de tu granja."',
     '"Controle o estoque de alimentos e produtos da sua fazenda."'),
    ('"Qué porción del presupuesto representa cada producto."',
     '"Qual parte do orçamento representa cada produto."'),
    ('"¿Qué insumo es?"',
     '"Qual insumo?"'),
    ('"Escribí el nombre exacto. Si ya existe, se suma al stock."',
     '"Digite o nome exato. Se já existir, será somado ao estoque."'),
    ('"Cantidad en kg"',               '"Quantidade em kg"'),
    ('"Cuántos kilos vas a ingresar."', '"Quantos quilos você vai cadastrar."'),
    ('"Precio por kg ($)"',             '"Preço por kg (R$)"'),
    ('"Cuánto pagaste por kilo. Opcional."',
     '"Quanto você pagou por quilo. Opcional."'),
    # ── Maquinário ────────────────────────────────────────────────────────
    ('"Registrá tus máquinas y llevá un historial de cada mantenimiento realizado."',
     '"Cadastre suas máquinas e mantenha um histórico de cada manutenção realizada."'),
    ('"Tipo de máquina"',               '"Tipo de máquina"'),
    ('"¿Para qué se usa principalmente?"', '"Para que é usada principalmente?"'),
    ('"Completá los datos principales. Solo el Nombre es obligatorio."',
     '"Preencha os dados principais. Somente o Nome é obrigatório."'),
    ('"Anotá cada revisión o reparación para llevar el historial al día."',
     '"Registre cada revisão ou reparo para manter o histórico atualizado."'),
    ('"¿A qué máquina le hiciste el mantenimiento?"',
     '"Qual máquina recebeu a manutenção?"'),
    ('"¿Qué clase de trabajo se realizó?"', '"Que tipo de trabalho foi realizado?"'),
    ('"Costo en pesos ($)"',              '"Custo (R$)"'),
    ('"Descripción del trabajo"',         '"Descrição do trabalho"'),
    ('"Detallá qué se hizo, qué piezas se cambiaron, etc."',
     '"Detalhe o que foi feito, quais peças foram trocadas, etc."'),
    ('"Cuándo hay que volver a hacerle servicio."',
     '"Quando será necessário fazer a próxima revisão."'),
    ('"Primero elegí la máquina a la que le hiciste el mantenimiento."',
     '"Primeiro escolha a máquina que recebeu a manutenção."'),
    # ── Reprodução ────────────────────────────────────────────────────────
    ('"Controlá las fechas de fertilización y hacé seguimiento de los partos esperados."',
     '"Controle as datas de fertilização e acompanhe os partos esperados."'),
    ('"¿A qué vaca?"',                   '"Qual vaca?"'),
    ('"Anotá el toro utilizado, la dosis, el proveedor o cualquier dato útil."',
     '"Anote o touro utilizado, a dose, o fornecedor ou qualquer dado útil."'),
    ('"Primero elegí el animal que fue fertilizado."',
     '"Primeiro escolha o animal que foi fertilizado."'),
    ('"¿Qué vaca parió?"',               '"Qual vaca pariu?"'),
    ('"Cuánto pesó al nacer. Podés dejarlo en 0 si no lo pesaron."',
     '"Quanto pesou ao nascer. Pode deixar 0 se não foi pesado."'),
    ('"Primero elegí la vaca que parió."', '"Primeiro escolha a vaca que pariu."'),
    ('"Registrá una fertilización para que aparezca aquí la fecha estimada de parto."',
     '"Registre uma fertilização para que apareça aqui a data estimada do parto."'),
    ('"Registrá la primera fertilización usando el formulario de arriba."',
     '"Registre a primeira fertilização usando o formulário acima."'),
    # ── Finanças ──────────────────────────────────────────────────────────
    ('"Registrá tus ingresos y gastos para saber cómo está la plata de tu granja."',
     '"Registre suas receitas e despesas para saber como está o dinheiro da sua fazenda."'),
    ('"que no están incluidos arriba. Podés cargarlos manualmente si querés verlos en el balance."',
     '"que não estão incluídos acima. Pode cadastrá-los manualmente para vê-los no balanço."'),
    ('"🍩 ¿En qué se fue el dinero?"',   '"🍩 Em que foi o dinheiro?"'),
    ('"Ingresá un ingreso (plata que entrá) o un gasto (plata que sale)."',
     '"Informe uma receita (dinheiro que entra) ou uma despesa (dinheiro que sai)."'),
    ('"¿De qué tipo es este movimiento?"', '"Que tipo é este movimento?"'),
    ('"Monto en pesos ($)"',             '"Valor (R$)"'),
    ('"¿Cuánto dinero fue? Solo el número, sin el signo $."',
     '"Qual o valor? Somente o número, sem o sinal R$."'),
    ('"Anotá los detalles para recordar de qué se trató."',
     '"Anote os detalhes para lembrar do que se tratou."'),
    ('"Están aquí como referencia — si querés incluirlos en el balance, cargalos manualmente arriba."',
     '"Estão aqui como referência — se quiser incluí-los no balanço, cadastre-os manualmente acima."'),
    ('"¿En qué se gastó el dinero?"',    '"Em que foi gasto o dinheiro?"'),
    # ── Funcionários ──────────────────────────────────────────────────────
    ('"Registrá tu personal, sus cargos y llevá el historial de pagos."',
     '"Cadastre seu pessoal, seus cargos e mantenha o histórico de pagamentos."'),
    ('"Completá los datos del nuevo integrante del equipo."',
     '"Preencha os dados do novo integrante da equipe."'),
    ('"¿Qué función cumple en la granja?"', '"Qual função exerce na fazenda?"'),
    # ── Relatórios ────────────────────────────────────────────────────────
    ('"Qué tipo de mantenimiento se realiza más."',
     '"Qual tipo de manutenção é realizado com mais frequência."'),
    # ── Outros remanescentes ──────────────────────────────────────────────
    ('"Tipo de manutenção"', '"Tipo de manutenção"'),  # already PT, keep
]

def run():
    path = "app/main.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    count = 0
    for old, new in TEXT_MAP2:
        if old in content:
            content = content.replace(old, new)
            count += 1

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"OK: {count} substituições adicionais aplicadas.")

if __name__ == "__main__":
    run()
