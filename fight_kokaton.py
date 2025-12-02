import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 爆弾の数
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  
    imgs = {  
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
        screen.blit(self.img, self.rct)



class Score:
    """
    スコア表示に関するクラス
    """
    def __init__(self):
        # フォント設定
        self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)  # 青
        self.score = 0            # 初期スコア
        self.update_img()

    def update_img(self):
        """現在のスコアから文字列Surfaceを作り直す"""
        self.img = self.fonto.render(f"スコア: {self.score}", True, self.color)
        self.rct = self.img.get_rect()
        self.rct.center = (100, HEIGHT - 50)

    def add(self, amount: int = 1):
        """スコアを増やして、画像を作り直す"""
        self.score += amount
        self.update_img()

    def update(self, screen: pg.Surface):
        """スコアの画像を描画する"""
        screen.blit(self.img, self.rct)



class  Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird:"Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        self.img = pg.image.load(f"fig/beam.png")  # Surface
        self.rct = self.img.get_rect()  # Rect
        self.rct.centery = bird.rct.centery  # ビームの中心縦座標 = こうかとんの中心縦座標
        self.rct.left = bird.rct.right  # ビームの左座標 = こうかとんの右座標
        self.vx, self.vy = +5, 0

    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)    


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)
        
class Explosion:
    """
    爆発エフェクトに関するクラス
    """
    def __init__(self, bomb: Bomb):
        # explosion.gif を読み込み
        img0 = pg.image.load("fig/explosion.gif")
        # 上下左右反転した画像も作る
        img1 = pg.transform.flip(img0, True, True)
        self.imgs = [img0, img1]

        # 爆発位置は「爆発した爆弾の中心」
        self.rct = self.imgs[0].get_rect()
        self.rct.center = bomb.rct.center

        # 表示時間（フレーム数）
        self.life = 20

    def update(self, screen: pg.Surface):
        """
        lifeを減らしながら爆発を描画
        """
        if self.life <= 0:
            return
        self.life -= 1

        # life の偶奇で画像を切り替えてチラチラさせる
        img = self.imgs[self.life % 2]
        screen.blit(img, self.rct)

def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))

    # 爆弾・ビーム・スコアの初期化
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    beams: list[Beam] = []   
    score = Score()
    explosions: list[Explosion] = []

    clock = pg.time.Clock()
    tmr = 0

    while True:
        # イベント処理
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下で Beam インスタンス生成（複数ビーム）
                beams.append(Beam(bird))   

        # 背景描画
        screen.blit(bg_img, [0, 0])

        # こうかとん vs 爆弾（ゲームオーバー判定）
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                bird.change_img(8, screen)
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2 - 150, HEIGHT//2])

                pg.display.update()
                time.sleep(1)
                return

            # ビーム vs 爆弾（複数ビーム＆複数爆弾）
        for i, beam in enumerate(beams):
            if beam is None:     
                continue
            for j, bomb in enumerate(bombs):
                if bomb is None:  
                    continue
                if beam.rct.colliderect(bomb.rct):
                    explosions.append(Explosion(bomb))

                    beams[i] = None       # このビームは削除予定
                    bombs[j] = None       # この爆弾も削除予定
                    bird.change_img(6, screen)
                    score.add(1)          # スコア +1


        # None を取り除いてリストを整理
        beams = [b for b in beams if b is not None]
        bombs = [b for b in bombs if b is not None]

        # こうかとんの移動
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)   

        # ビームを更新（リストの全ビームを描画）
        for beam in beams:
            beam.update(screen)

        alive_explosions = []
        for ex in explosions:
            ex.update(screen)
            if ex.life > 0:
                  alive_explosions.append(ex)
        explosions = alive_explosions

        # 爆弾の更新
        for bomb in bombs:
            bomb.update(screen)

        # スコア描画
        score.update(screen)

        pg.display.update()
        tmr += 1
        clock.tick(50)



if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()