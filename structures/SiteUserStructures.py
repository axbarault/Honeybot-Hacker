from abc import ABC

from discord import Embed


class SiteUser(ABC):

	def __init__(self, **kwargs):
		self.d_id = kwargs.get('d_id', None)
		self.d_name = kwargs.get('d_name', None)
		self.rm_id = kwargs.get('rm_id', None)  # Remote id
		self.rm_name = kwargs.get('rm_name', None)  # Remote name

	def assert_integrity(self) -> bool:
		assert self.d_id is not None and self.d_name is not None and self.rm_name is not None and self.rm_id is not None
		return True

	def fill_embed_fields(self, embed: Embed):
		embed.add_field(name="Compte Discord", value="<@%d>" % int(self.d_id))
		embed.add_field(name="Pseudo Site", value=self.rm_name)


class NewbieUser(SiteUser):

	@staticmethod
	def rank_to_kingdom(rank: int) -> str:
		ranks = {
			0: "unknown",
			10: "1337",
			50: "hax0r",
			350: 'challenger',
			1650: 'script kiddy',
			20000: 'kikoo'
		}
		for lb, kd in ranks.items():
			if rank <= lb:
				return kd
		return "péon"

	@property
	def rm_kingdom(self):
		return self.rank_to_kingdom(self.rm_pos) if self.rm_pos is not None else None

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.rm_pts = kwargs.get('rm_pts', None)  # Remote Points
		self.rm_pos = kwargs.get('rm_pos', None)  # Remote Position

	def assert_integrity(self) -> bool:
		super().assert_integrity()
		assert self.rm_pts is not None and self.rm_pos is not None
		return True

	def fill_embed_fields(self, embed: Embed):
		super().fill_embed_fields(embed)
		embed.add_field(name="", value="")  # Line break
		embed.add_field(name="Points", value=str(self.rm_pts))
		embed.add_field(name="Position", value=str(self.rm_pos) if self.rm_pos > 0 else "HC")
		embed.add_field(name="Royaume", value=self.rm_kingdom)


class RootMeUser(SiteUser):

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.rm_pts = kwargs.get('rm_pts', None)
		self.rm_challs = kwargs.get('rm_challs', 0)
		self.rm_pos = kwargs.get('rm_pos', None)
		self.rm_rank = kwargs.get('rm_rank', None)

	def assert_integrity(self) -> bool:
		super().assert_integrity()
		assert self.rm_pts is not None and self.rm_challs is not None and self.rm_pos is not None and self.rm_rank is not None
		return True

	def fill_embed_fields(self, embed: Embed):
		super().fill_embed_fields(embed)
		embed.add_field(name="Challenges", value=str(self.rm_challs))  # Line break
		embed.add_field(name="Points", value=str(self.rm_pts))
		embed.add_field(name="Position", value=str(self.rm_pos) if self.rm_pos > 0 else "HC")
		embed.add_field(name="Rang", value=self.rm_rank)


class LeetCodeUser(SiteUser):

	def __init__(self, **kwargs):
		kwargs['rm_id'] = -1  # No account id as far as I can tell for leetcode users
		super().__init__(**kwargs)
		self.rm_pos = kwargs.get('rm_pos', None)
		self.rm_avatar = kwargs.get('rm_avatar', None)
		self.rm_solved = [
			kwargs.get('rm_solved_0', None),
			kwargs.get('rm_solved_1', None),
			kwargs.get('rm_solved_2', None),
		]

	def assert_integrity(self) -> bool:
		assert self.d_id is not None and self.d_name is not None and self.rm_name is not None and None not in self.rm_solved
		return True

	def fill_embed_fields(self, embed: Embed):
		super().fill_embed_fields(embed)
		embed.add_field(name="Position", value=str(self.rm_pos))
		embed.add_field(name="// Facile", value=str(self.rm_solved[0]))
		embed.add_field(name="// Moyen", value=str(self.rm_solved[1]))
		embed.add_field(name="// Difficile", value=str(self.rm_solved[2]))
