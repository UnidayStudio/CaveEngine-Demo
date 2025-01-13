import cave

DEFAULT_LANGUAGE = 0

def SET_LANGUAGE(lang):
	global DEFAULT_LANGUAGE
	DEFAULT_LANGUAGE = lang

GAME_TEXTS = {
	"play demos" : ["Play Demos...", "Jogar Exemplos..."],

	"main menu" : ["Main Menu (Demo)", "Menu Principal (Demo)"],
	"paused" : ["Paused", "Paused"],
	"continue" : ["Continue", "Continuar"],
	"restart" : ["Restart", "Reiniciar"],
	"back to menu" : ["Back to Menu", "Voltar ao Menu"],

	"previous" : ["Previous...", "Anterior..."],
	"next" : ["Next...", "Próximo..."],

	"particle demos" : ["Particle Demos", "Demos de Partículas"],
	"save load" : ["Save/Load", "Salvar/Carregar"],
	"save" : ["Save", "Salvar"],
	"load" : ["Load", "Carregar"],

	"save pos" : ["Save Position", "Salvar Posição"],
	"load pos" : ["Load Position", "Carregar Posição"],

	"advanced demo" : ["Advanced Demo...", "Demo Avançado..."],

	"demo select" : ["Select a Demo:", "Selecione um Exemplo:"],
	"vehicle" : ["Vehicle Demo", "Carro"],
	"first person" : ["First Person", "Primeira Pessoa"],
	"third person" : ["Third Person", "Terceira Pessoa"],
	"top down"     : ["Top Down", "Top Down"],
	"minecraft"    : ["Minecraft", "Minecraft"],
	"online game"  : ["Online Game", "Jogo Online"],
	
	"language select" : ["Select a Language:", "Selecione um Idioma:"],
	"language" : ["Language...", "Idioma..."],
	"portuguese" : ["Portuguese", "Português"],
	"english" : ["English", "Inglês"],

	"quit game" : ["Quit Game", "Sair do Jogo"],

	"back" : ["Back...", "Voltar..."],
}


def LOCALIZE(ent):
	ui = ent.get("UI Element")
	if not ui:
		return
	text = GAME_TEXTS.get(ui.text)
	if text:
		ui.text = text[DEFAULT_LANGUAGE]
		

