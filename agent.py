import time
import math
from utils.ssl.Navigation import Navigation, Point
from utils.ssl.base_agent import BaseAgent


class ExampleAgent(BaseAgent):
    
    def __init__(self, id=0, yellow=False):
        super().__init__(id, yellow)
        self.setup_parameters()
        self.status_log = []  # Aqui tá a lista do painel de controle (Aprimorar isso porque ta infinito no terminal por algum motivo)

    def setup_parameters(self):
        # Configura os parâmetros dos jogadores
        self.last_avoidance_time = time.time()
        self.modo_evitar = False

        # Parâmetros de movimento do jogador
        self.parametros_movimento = {
            'fator_desaceleracao': 1,  # Desacela o jogador, não sei pq não ta desacelerando como eu quero entao deixei em 1
            'distancia_obstaculo_perto': 0.7,  # Distancia que o cara já ve o obstaculo
            'margem': 0.1  # Margem de segurança pra pegar o objetivo, 0.2 ele so nao pega por algum motivo wtf
        }

        # Parâmetro do objetivo e a faixa de distância do local do mesmo
        self.parametros_evitar = {
            'raio_distancia': (1, 0),
        }

        # Objetivos
        self.targets = []  # Aqui é a lista de onde os objetivos vão pra os robo ir ate la
        self.objetivo_atribuido = None  # Objetivo atual que o robo vai
        self.objetivos_visitados = set()  # Local onde já foi pisado pelo robo

    def raio_visao(self, target, max_distance=3):
        # Simula se tem obstáculos na linha reta até o local
        dx = target.x - self.robot.x
        dy = target.y - self.robot.y
        distancia_objetivo = self.calculo_distancia(target)

        if distancia_objetivo < max_distance:
            return distancia_objetivo  # Diz se o obstáculo foi ou não conquistado pra mostrar
        return float('inf')  # Não tem obstáculo no meio

    def choose_target(self):
        # Escolhe o objetivo mais próximo
        if not self.targets:
            return None, None

        # Aqui vai dizer onde o objetivo vai, do mais perto ao mais longe nessa ordem
        sorted_objetivos = sorted(self.targets, key=self.calculo_distancia)
        objetivo_perto = sorted_objetivos[0]  # Qual é o objetivo mais próximo

        # Limpeza e reorganização da lista de objetivos, ele vai ajeitar a lista de obj aqui
        self.targets.clear()
        self.targets.extend(sorted_objetivos)

        return objetivo_perto, self.calculo_distancia(objetivo_perto)

    def calculo_distancia(self, target):
        # Calcula a distância entre o agente e um objetivo
        dx = target.x - self.robot.x
        dy = target.y - self.robot.y
        return math.sqrt(dx**2 + dy**2)

    def move_towards_target(self, target, distance):
        # Move o jogador até o objetivo, diferenciando as coordenadas
        dx = target.x - self.robot.x
        dy = target.y - self.robot.y
        obstacle_distance = self.raio_visao(target)

        if obstacle_distance < float('inf'):
            self.modo_evitar = True
            velocidade_objetivo, target_angle_velocity = self.evitar_obstaculo(target)
        else:
            self.modo_evitar = False
            self.parametros_movimento['fator_desaceleracao'] = 1  # Aqui mudo a velocidade, 1 é a normal, abaixando fica mais lento
            velocidade_objetivo, target_angle_velocity = Navigation.goToPoint(self.robot, target)

        # Ajuste da velocidade
        velocidade_ajustada = Point(
            velocidade_objetivo.x * self.parametros_movimento['fator_desaceleracao'],
            velocidade_objetivo.y * self.parametros_movimento['fator_desaceleracao']
        )
        self.set_vel(velocidade_ajustada)
        self.set_angle_vel(target_angle_velocity)

    def evitar_obstaculo(self, target):
        # Desvia do obstáculo de forma tranquila (falta aprimorar isso, ta um desvio meio feio ainda)
        dx = target.x - self.robot.x
        dy = target.y - self.robot.y
        distancia_objetivo = self.calculo_distancia(target)

        # Cálculo da distância de desvio
        distancia_evitar = max(0.1, min(1, distancia_objetivo / 2))
        novo_objetivo_x = self.robot.x + distancia_evitar if dx >= 0 else self.robot.x - distancia_evitar
        novo_objetivo_y = self.robot.y + distancia_evitar if dy >= 0 else self.robot.y - distancia_evitar

        novo_objetivo = Point(novo_objetivo_x, novo_objetivo_y)
        return Navigation.goToPoint(self.robot, novo_objetivo)

    def objetivo(self):
        # Atribui um objetivo para o jogador
        objetivo_perto, distancia_perto = self.choose_target()

        if objetivo_perto is None:
            self.objetivo_atribuido = None
            self.set_vel(Point(0, 0))
            self.set_angle_vel(0)
            return

        if distancia_perto <= self.parametros_movimento['margem']:
            self.objetivos_visitados.add(objetivo_perto)  # Aqui diz que foi visitado
            self.targets.remove(objetivo_perto)  # Tira o objetivo que foi passado da lista de objetivos
            self.objetivo_atribuido = None
            self.set_vel(Point(0, 0))
            self.set_angle_vel(0)
        else:
            self.objetivo_atribuido = objetivo_perto

    def update_status(self):
        # Atualiza o status do jogador no painel de controle, aqui fica a estrutura do painel de controle
        self.status_log.clear()
        self.status_log.append(f"Jogador Camisa Nº: {self.id}")
        self.status_log.append(f"Posição: ({self.robot.x:.2f}, {self.robot.y:.2f})")

        if self.objetivo_atribuido:
            self.status_log.append(f"Objetivo: ({self.objetivo_atribuido.x:.2f}, {self.objetivo_atribuido.y:.2f})")
            self.status_log.append(f"Distância do objetivo: {self.calculo_distancia(self.objetivo_atribuido):.2f}")
            self.status_log.append(f"Está desviando: {'Sim' if self.modo_evitar else 'Não'}")
        else:
            self.status_log.append("Sem objetivo atribuído.")

    def display_status(self):
        # Fica mostrando o status do agente no terminal
        print("\n".join(self.status_log))

    def decision(self):
        self.objetivo()  # Aqui é onde fica o cérebro de decisão do jogador, basicamente o prime dele

        if self.objetivo_atribuido:
            self.move_towards_target(self.objetivo_atribuido, self.calculo_distancia(self.objetivo_atribuido))
        else:
            self.set_vel(Point(0, 0))
            self.set_angle_vel(0)

        self.update_status()
        self.display_status()

    def post_decision(self):
        # Vê o que fazer com essa parte amanhã (perguntar no discord)
        pass

