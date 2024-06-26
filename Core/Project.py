from .FileIO import readYaml, ScanDire, ScanSubDire
from .Library import Library
from .Resource import Resource
from .Styles import getStyleCode
from .Templates_Manager import TemplateManager
from .Code_Formatter import format_code
from .Debug import LogInfo, LogError, LogWarning, FormatXaml
import os

sep = os.path.sep
class Project:
    def load_plugins(self,plugin_path):
        '''加载插件'''
        for data,name,exten in ScanSubDire(plugin_path,'pack\.yml'):
            dire = os.path.dirname(data['file_path'])
            self.resources.loadResources(f'{dire}{sep}Resources','')
            
    def import_pack(self,path):
        '''导入资源包'''
        LogInfo(f'[Project] Start to import pack at: {path}')
        pack_info = readYaml(path)
        self.version = pack_info['version']
        self.default_page = pack_info.get('default_page')
        LogInfo(f'[Project] Pack version: {self.version}')
        self.base_path = os.path.dirname(path)
        LogInfo(f'[Project] Loading cards')
        self.base_library = Library(readYaml(f"{self.base_path}{sep}Libraries{sep}__LIBRARY__.yml"))
        LogInfo(f'[Project] Importing resources')
        self.resources.loadResources(f'{self.base_path}{sep}Resources','')
        LogInfo(f'[Project] Loading pages')
        for page in ScanDire(f'{self.base_path}{sep}Pages',r'.*'):
            self.import_page(page)
        
    def __init__(self,path):
        LogInfo(f'[Project] Initing ...')
        envpath = os.path.dirname(os.path.dirname(__file__))
        self.resources = Resource()
        LogInfo(f'[Project] Loading basic resources')
        self.resources.loadResources(f'{envpath}{sep}Resources','')
        LogInfo(f'[Project] Loading plugins')
        self.load_plugins(f'{envpath}{sep}Plugin')
        self.pages = {}
        self.import_pack(path)
        self.TemplateManager = TemplateManager(self.resources)
        LogInfo(f'[Project] Pack loaded successful!')
    
    def import_page(self,page_tuple):
        page, file_name, file_exten = page_tuple
        if file_exten == 'yml':
            if 'name' in page:
                self.pages.update({ page['name']:page })
            self.pages.update({file_name:page})
            if 'alias' in page:
                for alias in page.get('alias'):
                    self.pages.update({alias:page})
        elif file_exten == 'xaml':
            self.pages.update({file_name:{'xaml':page}})
        else:
            LogWarning(f'[Project] Page file not supported: {file_name}.{file_exten}')

    def get_page_xaml(self,page_alias):
        '''获取 xaml 代码'''
        LogInfo(f'[Project] Getting codes of page: {page_alias}')
        if page_alias not in self.pages:
            raise PageNotFoundError(LogError(f'[Project] Cannot find page named "{page_alias}"'))
        content_xaml = ''
        page = self.pages[page_alias]
        if 'xaml' in page:
            return page['xaml']
        for card_ref in page['cards']:
            card_ref = format_code(card_ref,{},self.resources,'')
            LogInfo(f'[Project] Get card: {card_ref}')
            card_ref = card_ref.replace(' ','').split('|')
            if card_ref[0] == '':
                continue
            try:
                card = self.base_library.getCard(card_ref[0],False)
            except:
                LogWarning(f'[Project] 获取卡片失败')
                continue
            if len(card_ref) > 1:
                for arg in card_ref[1:]:
                    argname,argvalue = arg.split('=')
                    card[argname] = argvalue
            card_xaml = self.TemplateManager.build(card)
            #card_xaml = format_code(card_xaml,card,self.resources.scripts)
            content_xaml += card_xaml
        page_xaml = self.resources.page_templates['Default']
        page_xaml = page_xaml.replace('${animations}','') # TODO
        page_xaml = page_xaml.replace('${styles}',getStyleCode(self.resources.styles))
        page_xaml = page_xaml.replace('${content}',content_xaml)
        return page_xaml
    
    def get_page_name(self,page_alias):
        '''获取页面名'''
        if page_alias not in self.pages:
            raise PageNotFoundError(LogError(f'[Project] Cannot find page named "{page_alias}"'))
        page = self.pages[page_alias]
        return page.get('name')
class PageNotFoundError(Exception):
    pass