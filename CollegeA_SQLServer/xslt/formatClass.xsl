<?xml version="1.0" encoding="UTF-8"?>
<!-- 课程信息格式转换: 学院原生格式 → 标准集成格式 -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <Classes>
      <xsl:for-each select="Classes/class">
        <class>
          <!-- 课程号映射 -->
          <id>
            <xsl:choose>
              <xsl:when test="Cno"><xsl:value-of select="Cno"/></xsl:when>
              <xsl:when test="cno"><xsl:value-of select="cno"/></xsl:when>
              <xsl:otherwise><xsl:value-of select="id"/></xsl:otherwise>
            </xsl:choose>
          </id>
          <!-- 课程名映射 -->
          <name>
            <xsl:choose>
              <xsl:when test="Cnm"><xsl:value-of select="Cnm"/></xsl:when>
              <xsl:when test="cname"><xsl:value-of select="cname"/></xsl:when>
              <xsl:otherwise><xsl:value-of select="name"/></xsl:otherwise>
            </xsl:choose>
          </name>
          <!-- 学分映射 -->
          <score>
            <xsl:choose>
              <xsl:when test="Ctm"><xsl:value-of select="Ctm"/></xsl:when>
              <xsl:when test="credit"><xsl:value-of select="credit"/></xsl:when>
              <xsl:otherwise><xsl:value-of select="score"/></xsl:otherwise>
            </xsl:choose>
          </score>
          <!-- 教师映射 -->
          <teacher>
            <xsl:choose>
              <xsl:when test="Tec"><xsl:value-of select="Tec"/></xsl:when>
              <xsl:when test="teacher"><xsl:value-of select="teacher"/></xsl:when>
              <xsl:otherwise><xsl:value-of select="teacher"/></xsl:otherwise>
            </xsl:choose>
          </teacher>
          <!-- 地点映射 -->
          <location>
            <xsl:choose>
              <xsl:when test="Pla"><xsl:value-of select="Pla"/></xsl:when>
              <xsl:when test="address"><xsl:value-of select="address"/></xsl:when>
              <xsl:otherwise><xsl:value-of select="location"/></xsl:otherwise>
            </xsl:choose>
          </location>
          <!-- 共享来源 -->
          <share>
            <xsl:choose>
              <xsl:when test="Share"><xsl:value-of select="Share"/></xsl:when>
              <xsl:when test="share"><xsl:value-of select="share"/></xsl:when>
              <xsl:otherwise><xsl:value-of select="share"/></xsl:otherwise>
            </xsl:choose>
          </share>
        </class>
      </xsl:for-each>
    </Classes>
  </xsl:template>

</xsl:stylesheet>
