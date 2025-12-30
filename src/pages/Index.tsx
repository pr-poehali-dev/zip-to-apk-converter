import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import Icon from '@/components/ui/icon';
import { useToast } from '@/hooks/use-toast';

const Index = () => {
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [iconFile, setIconFile] = useState<File | null>(null);
  const [appName, setAppName] = useState('');
  const [appVersion, setAppVersion] = useState('');
  const [isConverting, setIsConverting] = useState(false);
  const [progress, setProgress] = useState(0);
  const { toast } = useToast();

  const handleZipChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.name.endsWith('.zip')) {
      setZipFile(file);
    } else {
      toast({
        variant: "destructive",
        title: "Ошибка",
        description: "Пожалуйста, выберите ZIP-архив"
      });
    }
  };

  const handleIconChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'image/png') {
      const img = new Image();
      img.onload = () => {
        if (img.width === 512 && img.height === 512) {
          setIconFile(file);
        } else {
          toast({
            variant: "destructive",
            title: "Неверный размер",
            description: "Иконка должна быть 512×512 пикселей"
          });
        }
      };
      img.src = URL.createObjectURL(file);
    } else {
      toast({
        variant: "destructive",
        title: "Ошибка",
        description: "Пожалуйста, выберите PNG-файл"
      });
    }
  };

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = error => reject(error);
    });
  };

  const handleConvert = async () => {
    if (!zipFile || !iconFile || !appName || !appVersion) {
      toast({
        variant: "destructive",
        title: "Заполните все поля",
        description: "Все поля обязательны для заполнения"
      });
      return;
    }

    setIsConverting(true);
    setProgress(0);

    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 500);

    try {
      const zipBase64 = await fileToBase64(zipFile);
      const iconBase64 = await fileToBase64(iconFile);
      
      const func2url = await fetch('/func2url.json').then(r => r.json());
      const apiUrl = func2url['html-to-apk'];
      
      if (!apiUrl) {
        throw new Error('Backend функция не найдена');
      }

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          appName,
          appVersion,
          zipFile: zipBase64,
          iconFile: iconBase64
        })
      });

      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text();
        throw new Error(`Сервер вернул неверный формат данных. Ожидался JSON, получен: ${contentType || 'unknown'}`);
      }

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Ошибка конвертации');
      }
      
      setProgress(100);
      clearInterval(progressInterval);
      
      const apkData = result.apkFile;
      const fileName = result.fileName || `${appName.replace(/\s+/g, '_')}_v${appVersion}.apk`;
      
      const link = document.createElement('a');
      link.href = `data:application/vnd.android.package-archive;base64,${apkData}`;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast({
        title: "Успешно!",
        description: "APK-файл скачивается"
      });

    } catch (error) {
      clearInterval(progressInterval);
      toast({
        variant: "destructive",
        title: "Ошибка конвертации",
        description: error instanceof Error ? error.message : "Попробуйте снова"
      });
    } finally {
      setIsConverting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-muted/30 to-background">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-foreground mb-3 tracking-tight">
              HTML → APK Конвертер
            </h1>
            <p className="text-muted-foreground text-lg">
              Профессиональный инструмент конвертации веб-приложений
            </p>
          </div>

          <Card className="border-border shadow-sm">
            <CardHeader className="border-b border-border/50">
              <CardTitle className="text-2xl font-semibold">Параметры приложения</CardTitle>
              <CardDescription className="text-base">
                Заполните все поля для создания APK-файла
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              <div className="space-y-2">
                <Label htmlFor="app-name" className="text-sm font-medium">
                  Название приложения
                </Label>
                <Input
                  id="app-name"
                  placeholder="Моё приложение"
                  value={appName}
                  onChange={(e) => setAppName(e.target.value)}
                  className="h-11"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="app-version" className="text-sm font-medium">
                  Версия приложения
                </Label>
                <Input
                  id="app-version"
                  placeholder="1.0.0"
                  value={appVersion}
                  onChange={(e) => setAppVersion(e.target.value)}
                  className="h-11"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="zip-file" className="text-sm font-medium">
                  ZIP-архив с HTML
                </Label>
                <div className="relative">
                  <Input
                    id="zip-file"
                    type="file"
                    accept=".zip"
                    onChange={handleZipChange}
                    className="h-11 cursor-pointer file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-medium file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
                  />
                  {zipFile && (
                    <div className="mt-2 flex items-center text-sm text-muted-foreground">
                      <Icon name="CheckCircle" size={16} className="mr-2 text-green-600" />
                      {zipFile.name}
                    </div>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="icon-file" className="text-sm font-medium">
                  Иконка приложения (512×512 PNG)
                </Label>
                <div className="relative">
                  <Input
                    id="icon-file"
                    type="file"
                    accept="image/png"
                    onChange={handleIconChange}
                    className="h-11 cursor-pointer file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-medium file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
                  />
                  {iconFile && (
                    <div className="mt-2 flex items-center text-sm text-muted-foreground">
                      <Icon name="CheckCircle" size={16} className="mr-2 text-green-600" />
                      {iconFile.name}
                    </div>
                  )}
                </div>
              </div>

              {isConverting && (
                <div className="space-y-2 pt-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Прогресс конвертации</span>
                    <span className="font-medium">{progress}%</span>
                  </div>
                  <Progress value={progress} className="h-2" />
                </div>
              )}

              <Button 
                onClick={handleConvert}
                disabled={isConverting || !zipFile || !iconFile || !appName || !appVersion}
                className="w-full h-12 text-base font-medium"
                size="lg"
              >
                {isConverting ? (
                  <>
                    <Icon name="Loader2" className="mr-2 h-5 w-5 animate-spin" />
                    Конвертация...
                  </>
                ) : (
                  <>
                    <Icon name="Package" className="mr-2 h-5 w-5" />
                    Создать APK
                  </>
                )}
              </Button>

              <div className="pt-4 border-t border-border/50">
                <div className="flex items-start space-x-3 text-sm text-muted-foreground">
                  <Icon name="Info" size={18} className="mt-0.5 flex-shrink-0" />
                  <p>
                    Конвертер преобразует ваш HTML-сайт в нативное Android-приложение. 
                    Убедитесь, что все ресурсы упакованы в ZIP-архив.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="mt-8 grid grid-cols-3 gap-6">
            <div className="text-center space-y-2">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                <Icon name="FileArchive" className="text-primary" size={24} />
              </div>
              <p className="text-sm font-medium">Загрузите ZIP</p>
              <p className="text-xs text-muted-foreground">С HTML-файлами</p>
            </div>
            <div className="text-center space-y-2">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                <Icon name="Settings" className="text-primary" size={24} />
              </div>
              <p className="text-sm font-medium">Настройте</p>
              <p className="text-xs text-muted-foreground">Параметры приложения</p>
            </div>
            <div className="text-center space-y-2">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                <Icon name="Download" className="text-primary" size={24} />
              </div>
              <p className="text-sm font-medium">Скачайте APK</p>
              <p className="text-xs text-muted-foreground">Готовое приложение</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;