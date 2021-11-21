from nextcord.ext import commands
import nextcord



class ModCog(commands.Cog): 

    def warnusersAppend(self, userid, reason):
        with open(f'warnedusers.txt', 'a+', newline='') as userfile:
            userfile.write(f'{userid} warned for: {reason}\n')

    @commands.command()
    @commands.has_role('Moderator')
    async def ban(self, ctx, user, *, reason=None):
        user = ctx.message.mentions[0]
        if reason == None:
            reason = "No reason provided." 
        if ctx.author.id == user.id:
            await ctx.send("dont ban yourself")
            return
        await user.send(f'You have been banned from {ctx.guild} for {reason}')
        await ctx.guild.ban(user, delete_message_days=0, reason=reason)
        await ctx.send(f"{user} has been banned for: \n{reason}")
        
        
    @commands.command()
    @commands.has_role('Moderator')
    async def warn(self, ctx, user, *, reason):
        user = ctx.message.mentions[0]
        await user.send(f'You have been warned in {ctx.guild} for {reason}.\nPlease refrain from doing that in the future, thank you.')
        self.warnusersAppend(user.id, reason)
        await ctx.send(f"{user} has been warned for: \n{reason}")
        
        
    @commands.command()
    @commands.has_role('Moderator')
    async def warns(self, ctx, user):
        user = ctx.message.mentions[0]
        userfile = open(f'warnedusers.txt', 'r', newline='')
        warn_number = 0
        output = f"{user}'s warns are: ```"
        for line in userfile:
            if str(user.id) in line:
                reason = line[line.find(': ')+1:line.find('\n')]
                warn_number += 1
                output += f"{warn_number}.) {reason}"
        output += '```'
        await ctx.send(output)
    
    @commands.command()
    @commands.has_role('Moderator')
    async def unban(self, ctx, user, *, reason=None):
        user = ctx.message.mentions[0]
        if reason == None:
            reason = "No reason provided." 
        await ctx.guild.unban(user, reason=reason)
        await ctx.send(f"{user} has been unbanned for: \n{reason}")
def setup(bot):
    bot.add_cog(ModCog(bot))    